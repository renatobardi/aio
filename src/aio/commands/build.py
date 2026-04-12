"""AIO `build` command — full 5-step pipeline (M1)."""
# NOTE: NO `from __future__ import annotations` in this file.
# Typer relies on runtime type introspection; postponed evaluation breaks it.

import dataclasses
import importlib.resources
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mistune
import typer

from aio._log import get_logger
from aio._utils import base64_inline, build_jinja_env, escape_script
from aio._validators import check_external_urls, yaml_safe_load
from aio.composition.engine import CompositionEngine
from aio.composition.metadata import BuildResult, ComposedSlide, SlideRenderContext
from aio.exceptions import ExternalURLError, ParseError

_log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class DeckFrontmatter:
    """YAML front-matter extracted from the first --- block of slides.md."""

    title: str = "Untitled"
    author: str | None = None
    theme: str = "minimal"
    agent: str = "claude"


@dataclass
class SlideAST:
    """Parsed representation of a single slide."""

    index: int
    frontmatter: dict[str, Any]
    title: str | None
    body_tokens: list[Any]
    metadata: dict[str, str]
    raw_markdown: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Trailing whitespace stripped via .strip() on captured groups — avoids \s*.*?\s* backtracking
_TAG_RE = re.compile(r"<!--\s*@(\w[\w-]*):\s*(.*?)-->")
_HEADING_RE = re.compile(r"^#+\s+(.+)$", re.MULTILINE)

# Minimal SVG placeholder for missing images
_MISSING_IMAGE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="150">'
    '<rect width="200" height="150" fill="#f0f0f0"/>'
    '<text x="100" y="80" text-anchor="middle" fill="#999" font-size="14">Image not found</text>'
    "</svg>"
)


def _split_slides(content: str) -> tuple[dict[str, Any], list[str]]:
    """Split content on '\\n---\\n' into (frontmatter_dict, body_blocks)."""
    content = content.strip()
    frontmatter: dict[str, Any] = {}

    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            yaml_block = content[3:end].strip()
            try:
                frontmatter = yaml_safe_load(yaml_block, source="slides.md frontmatter") or {}
            except ParseError:
                raise
            content = content[end + 4 :].strip()

    blocks = re.split(r"\n---\n", content)
    blocks = [b.strip() for b in blocks if b.strip()]
    return frontmatter, blocks


def _extract_metadata(block: str) -> tuple[dict[str, str], str]:
    """Extract @key: value tags from HTML comments."""
    metadata: dict[str, str] = {}
    for match in _TAG_RE.finditer(block):
        key = match.group(1).strip()
        value = match.group(2).strip()
        if not key:
            continue
        metadata[key] = value
    cleaned = _TAG_RE.sub("", block).strip()
    return metadata, cleaned


def _render_markdown(text: str) -> str:
    """Convert Markdown to HTML using mistune."""
    md = mistune.create_markdown()
    result = md(text)
    return result if isinstance(result, str) else ""


def _load_vendor_js() -> str:
    """Load reveal.js from the vendor package."""
    try:
        ref = importlib.resources.files("aio.vendor.revealjs").joinpath("reveal.js")
        return ref.read_text(encoding="utf-8")
    except Exception as exc:
        _log.warning("Could not load vendor reveal.js: %s", exc)
        return "/* reveal.js not found */"


# ---------------------------------------------------------------------------
# Step 1: PARSE
# ---------------------------------------------------------------------------


def parse_slides(path: str | Path) -> list[SlideAST]:
    """Parse a slides.md file into a list of SlideAST objects."""
    file_path = Path(path)
    content = file_path.read_text(encoding="utf-8")
    _log.debug("Parsing %s (%d bytes)", file_path, len(content))

    frontmatter, blocks = _split_slides(content)
    _log.debug("Parsed frontmatter: %s; %d slide blocks", frontmatter, len(blocks))

    slides: list[SlideAST] = []
    for i, block in enumerate(blocks):
        metadata, cleaned = _extract_metadata(block)
        heading_match = _HEADING_RE.search(cleaned)
        title: str | None = heading_match.group(1) if heading_match else None

        try:
            md = mistune.create_markdown(renderer=None)
            tokens = md(cleaned) or []
        except Exception as exc:
            _log.warning("Mistune tokenization warning for slide %d: %s", i, exc)
            tokens = []

        slides.append(
            SlideAST(
                index=i,
                frontmatter=frontmatter,
                title=title,
                body_tokens=tokens if isinstance(tokens, list) else [],
                metadata=metadata,
                raw_markdown=cleaned,
            )
        )
        _log.debug("Slide %d: layout=%s, title=%s", i, metadata.get("layout"), title)

    _log.info("Parsed %d slides from %s", len(slides), file_path.name)
    return slides


# ---------------------------------------------------------------------------
# Step 2: ANALYZE
# ---------------------------------------------------------------------------


def analyze_slides(
    asts: list[SlideAST],
    theme_id: str = "minimal",
) -> list[SlideRenderContext]:
    """
    Resolve layouts and build SlideRenderContext for each slide.

    Unknown explicit layout IDs → CONTENT with WARNING (no crash).
    """
    engine = CompositionEngine()
    contexts: list[SlideRenderContext] = []

    for ast in asts:
        layout_type = engine.infer_layout(ast)
        body_html = _render_markdown(ast.raw_markdown) if ast.raw_markdown else ""

        # Resolve image_src: base64 inline or SVG placeholder
        image_path_str = ast.metadata.get("image")
        image_src: str | None = None
        if image_path_str:
            try:
                image_src = base64_inline(Path(image_path_str))
            except FileNotFoundError:
                _log.warning("Image not found: %s — using placeholder", image_path_str)
                image_src = "data:image/svg+xml;charset=utf-8," + _MISSING_IMAGE_SVG.replace("<", "%3C").replace(
                    ">", "%3E"
                )

        ctx = SlideRenderContext(
            slide_index=ast.index,
            slide_id=f"slide-{ast.index}",
            layout_id=layout_type.value,
            is_inferred=(ast.metadata.get("layout", "auto") in ("", "auto")),
            title=ast.title or ast.metadata.get("title"),
            body_html=body_html,
            speaker_notes=ast.metadata.get("notes"),
            stat_value=ast.metadata.get("stat"),
            stat_label=ast.metadata.get("label"),
            stat_description=ast.metadata.get("description"),
            quote_text=ast.metadata.get("quote"),
            quote_attribution=ast.metadata.get("author"),
            image_src=image_src,
            image_alt=ast.metadata.get("alt"),
            image_position=ast.metadata.get("image-position", "right"),
            cta_text=ast.metadata.get("cta"),
            left_title=ast.metadata.get("left-title"),
            left_content=ast.metadata.get("left-content"),
            right_title=ast.metadata.get("right-title"),
            right_content=ast.metadata.get("right-content"),
        )
        contexts.append(ctx)
        _log.debug("Slide %d: layout=%s (inferred=%s)", ast.index, layout_type.value, ctx.is_inferred)

    return contexts


# ---------------------------------------------------------------------------
# Step 3: COMPOSE
# ---------------------------------------------------------------------------


def compose_slides(contexts: list[SlideRenderContext]) -> list[ComposedSlide]:
    """
    Render each SlideRenderContext using its Jinja2 layout template.

    Validates html_fragment structure. Sanitizes SVG content.
    """
    env = build_jinja_env("aio.layouts")
    engine = CompositionEngine()
    composed: list[ComposedSlide] = []
    warnings: list[str] = []

    for ctx in contexts:
        template_name = ctx.layout_id.replace("-", "_") + ".j2"
        try:
            tmpl = env.get_template(template_name)
        except Exception:
            _log.warning("Template '%s' not found, falling back to content.j2", template_name)
            warnings.append(f"Slide {ctx.slide_index}: template '{template_name}' not found")
            try:
                tmpl = env.get_template("content.j2")
                ctx = dataclasses.replace(ctx, layout_id="content")
            except Exception as exc2:
                _log.error("content.j2 also missing: %s", exc2)
                continue

        # Render context as flat kwargs
        ctx_dict = dataclasses.asdict(ctx)
        html = tmpl.render(**ctx_dict)

        # Sanitize any embedded SVG
        if "<svg" in html:
            html = engine.sanitize_svg(html) or html

        slide_warnings = list(warnings)
        try:
            composed.append(
                ComposedSlide(
                    index=ctx.slide_index,
                    layout_id=ctx.layout_id,
                    html_fragment=html,
                    render_context=ctx,
                    warnings=slide_warnings,
                )
            )
        except ValueError as exc:
            _log.warning("Slide %d composition validation failed: %s", ctx.slide_index, exc)
            # Fallback: wrap in minimal section if validation fails
            fallback = f'<section data-layout="{ctx.layout_id}" class="layout-{ctx.layout_id}"></section>'
            composed.append(
                ComposedSlide(
                    index=ctx.slide_index,
                    layout_id=ctx.layout_id,
                    html_fragment=fallback,
                    render_context=ctx,
                    warnings=[str(exc)],
                )
            )

        _log.debug("Composed slide %d (%s)", ctx.slide_index, ctx.layout_id)

    return composed


# ---------------------------------------------------------------------------
# Step 4: RENDER
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
{theme_css}
{layout_css}
  </style>
</head>
<body class="reveal">
  <div class="slides">
{slides}
  </div>
  <script>
{vendor_js}
  </script>
  <script>
    Reveal.initialize({{
      controls: true,
      progress: true,
      center: true,
      hash: true,
      transition: 'slide'
    }});
  </script>
</body>
</html>
"""


def render_document(
    slides: list[ComposedSlide],
    theme_id: str = "minimal",
    title: str = "Presentation",
) -> str:
    """
    Assemble the full Reveal.js HTML document.

    All CSS and JS are inlined — no external resource references.
    """
    from aio.themes.loader import load_registry

    # Load theme CSS
    registry = load_registry()
    record = next((r for r in registry if r.id == theme_id), None)
    if record is None:
        _log.warning("Theme '%s' not found, using empty CSS", theme_id)
        theme_css = ""
        layout_css = ""
    else:
        theme_css = record.css_path.read_text(encoding="utf-8") if record.css_path.exists() else ""
        layout_css = record.layout_css_path.read_text(encoding="utf-8") if record.layout_css_path.exists() else ""

    vendor_js = escape_script(_load_vendor_js())
    slides_html = "\n".join(f"    {s.html_fragment}" for s in slides)

    html = _HTML_TEMPLATE.format(
        title=title,
        theme_css=theme_css,
        layout_css=layout_css,
        vendor_js=vendor_js,
        slides=slides_html,
    )
    return html


# ---------------------------------------------------------------------------
# Step 5: INLINE
# ---------------------------------------------------------------------------


def inline_assets(
    html: str,
    source_dir: Path,
    serve_mode: bool = False,
) -> str:
    """
    Verify no external URLs remain; append SSE snippet in serve_mode.

    Raises ExternalURLError if any https?:// URLs are found in src/href.
    """
    external = check_external_urls(html)
    if external:
        raise ExternalURLError(external)

    if serve_mode:
        sse_snippet = (
            "\n<script>\n"
            "  var __sse = new EventSource('/__sse__');\n"
            "  __sse.onmessage = function(e) {\n"
            "    var d = JSON.parse(e.data);\n"
            "    if (d.type === 'reload') window.location.reload();\n"
            "  };\n"
            "<\\/script>\n"
        )
        html = html.replace("</body>", sse_snippet + "</body>")

    return html


# ---------------------------------------------------------------------------
# Public API: build_pipeline
# ---------------------------------------------------------------------------


def build_pipeline(
    input_path: Path,
    output: Path,
    theme_id: str = "minimal",
    dry_run: bool = False,
    serve_mode: bool = False,
) -> BuildResult:
    """
    Run the full 5-step build pipeline.

    Steps: PARSE → ANALYZE → COMPOSE → RENDER → INLINE

    Returns BuildResult. Raises ExternalURLError (exit 3) if external URLs found.
    """
    start = time.perf_counter()

    # Step 1: PARSE
    _log.info("Step 1/5: PARSE")
    slides_ast = parse_slides(input_path)
    deck_fm = slides_ast[0].frontmatter if slides_ast else {}
    effective_theme = theme_id or deck_fm.get("theme", "minimal")
    title = str(deck_fm.get("title", "Presentation"))

    # Step 2: ANALYZE
    _log.info("Step 2/5: ANALYZE")
    contexts = analyze_slides(slides_ast, theme_id=effective_theme)

    # Step 3: COMPOSE
    _log.info("Step 3/5: COMPOSE")
    composed = compose_slides(contexts)

    # Step 4: RENDER
    _log.info("Step 4/5: RENDER")
    html = render_document(composed, theme_id=effective_theme, title=title)

    # Step 5: INLINE
    _log.info("Step 5/5: INLINE")
    html = inline_assets(html, source_dir=input_path.parent, serve_mode=serve_mode)

    elapsed = time.perf_counter() - start
    byte_size = len(html.encode("utf-8"))

    # Build histogram
    histogram: dict[str, int] = {}
    total_warnings = 0
    for s in composed:
        histogram[s.layout_id] = histogram.get(s.layout_id, 0) + 1
        total_warnings += len(s.warnings)

    result = BuildResult(
        output_path=output,
        slide_count=len(composed),
        byte_size=byte_size,
        theme_id=effective_theme,
        elapsed_seconds=elapsed,
        layout_histogram=histogram,
        warning_count=total_warnings,
    )

    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding="utf-8")
        _log.info("Built: %s (%d slides, %.1f KB)", output, len(composed), byte_size / 1024)

    return result


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------

app = typer.Typer()


@app.command()
def build(
    input: Path = typer.Argument(Path("slides.md"), help="Input slides.md path"),
    output: Path = typer.Option(Path("build/slides.html"), "--output", "-o", help="Output HTML path"),
    theme: str | None = typer.Option(None, "--theme", "-t", help="Theme override"),
    enrich: bool = typer.Option(False, "--enrich", help="Enable AI image generation"),
    provider: str = typer.Option("pollinations", "--provider", help="Image generation provider"),
    skip_existing: bool = typer.Option(False, "--skip-existing", help="Skip already-generated images"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Agent override"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show planned output without writing"),
) -> None:
    """Compile slides.md → build/slides.html."""
    # Auto-detect theme from project config if not overridden
    effective_theme = theme
    if not effective_theme:
        try:
            from aio._utils import find_aio_dir
            from aio.commands.init import ProjectConfig

            aio_dir = find_aio_dir(input.parent if input.parent != Path(".") else Path.cwd())
            cfg = ProjectConfig.load(aio_dir)
            effective_theme = cfg.theme
        except Exception:
            effective_theme = "minimal"

    effective_theme = effective_theme or "minimal"

    try:
        result = build_pipeline(input, output=output, theme_id=effective_theme, dry_run=dry_run)
    except ExternalURLError as exc:
        _log.error("External URLs found in output: %s", exc)
        typer.echo(f"Build failed: external URLs detected — {exc}", err=True)
        raise typer.Exit(code=3)
    except Exception as exc:
        _log.error("Build failed: %s", exc)
        typer.echo(f"Build failed: {exc}", err=True)
        raise typer.Exit(code=1)

    if dry_run:
        typer.echo(f"[dry-run] Would write {result.slide_count} slides ({result.byte_size / 1024:.1f} KB) to {output}")
    else:
        typer.echo(f"Built: {output} ({result.slide_count} slides, {result.byte_size / 1024:.1f} KB)")
    _log.info("Command complete")
