"""AIO `build` command — slide parser (US4) + build pipeline stub (M1)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mistune
import typer

from aio._log import get_logger
from aio._validators import yaml_safe_load
from aio.exceptions import ParseError

_log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Data models (T049, T050)
# ---------------------------------------------------------------------------


@dataclass
class DeckFrontmatter:
    """YAML front-matter extracted from the first --- block of slides.md."""

    title: str = "Untitled"
    author: str | None = None
    theme: str = "default"
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
# Internal helpers (T051, T052)
# ---------------------------------------------------------------------------

_TAG_RE = re.compile(r"<!--\s*@(\w+):\s*(.*?)\s*-->")
_HEADING_RE = re.compile(r"^#+\s+(.+)$", re.MULTILINE)


def _split_slides(content: str) -> tuple[dict[str, Any], list[str]]:
    """Split content on '\\n---\\n' into (frontmatter_dict, body_blocks).

    The first block is always the YAML frontmatter header.
    Raises ParseError on invalid YAML.
    """
    # Normalize: strip leading/trailing whitespace
    content = content.strip()

    # Extract optional YAML frontmatter (between first pair of ---)
    frontmatter: dict[str, Any] = {}
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            yaml_block = content[3:end].strip()
            try:
                frontmatter = yaml_safe_load(yaml_block, source="slides.md frontmatter") or {}
            except ParseError:
                raise
            # Remaining content after frontmatter
            content = content[end + 4:].strip()  # skip the closing ---

    # Split remaining content on slide separators
    # A separator is either "---" alone on a line surrounded by blank lines,
    # or simply "\n---\n"
    blocks = re.split(r"\n---\n", content)
    # Filter empty blocks that appear from trailing ---
    blocks = [b.strip() for b in blocks if b.strip()]

    return frontmatter, blocks


def _extract_metadata(block: str) -> tuple[dict[str, str], str]:
    """Extract @key: value tags from HTML comments.

    Returns (metadata_dict, cleaned_block) with tags removed.
    Silently ignores malformed tags (empty key).
    """
    metadata: dict[str, str] = {}
    cleaned = block

    for match in _TAG_RE.finditer(block):
        key = match.group(1).strip()
        value = match.group(2).strip()
        if not key:
            _log.warning("Malformed @tag with empty key — skipping: %s", match.group(0))
            continue
        metadata[key] = value

    # Strip all @tag comments from the block
    cleaned = _TAG_RE.sub("", cleaned).strip()
    return metadata, cleaned


# ---------------------------------------------------------------------------
# Public API (T053)
# ---------------------------------------------------------------------------


def parse_slides(path: str | Path) -> list[SlideAST]:
    """Parse a slides.md file into a list of SlideAST objects.

    Steps:
    1. Read file
    2. Split on frontmatter + slide separators
    3. Extract @metadata tags from each slide block
    4. Tokenize body via mistune
    5. Construct SlideAST per slide

    Raises ParseError on invalid YAML frontmatter.
    """
    file_path = Path(path)
    content = file_path.read_text(encoding="utf-8")
    _log.debug("Parsing %s (%d bytes)", file_path, len(content))

    frontmatter, blocks = _split_slides(content)
    _log.debug("Parsed frontmatter: %s; %d slide blocks", frontmatter, len(blocks))

    # Build mistune tokenizer (returns AST tokens, not HTML)
    md = mistune.create_markdown(renderer=None)

    slides: list[SlideAST] = []
    for i, block in enumerate(blocks):
        metadata, cleaned = _extract_metadata(block)

        # Extract title from first heading
        heading_match = _HEADING_RE.search(cleaned)
        title: str | None = heading_match.group(1) if heading_match else None

        # Tokenize markdown body
        try:
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
# CLI command stub
# ---------------------------------------------------------------------------

app = typer.Typer()


@app.command()
def build(
    input: Path = typer.Argument(Path("slides.md"), help="Input slides.md path"),
    output: Path = typer.Option(Path("build/slides.html"), "--output", "-o", help="Output HTML path"),
    theme: str = typer.Option(None, "--theme", "-t", help="Theme override"),
    enrich: bool = typer.Option(False, "--enrich", help="Enable AI image generation"),
    provider: str = typer.Option("pollinations", "--provider", help="Image generation provider"),
    skip_existing: bool = typer.Option(False, "--skip-existing", help="Skip already-generated images"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent override"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show planned output without writing"),
) -> None:
    """Compile slides.md → build/slides.html."""
    # Config auto-load (US5 — T057)
    try:
        from aio._utils import find_aio_dir
        from aio.commands.init import ProjectConfig

        aio_dir = find_aio_dir(input.parent if input.parent != Path(".") else Path.cwd())
        cfg = ProjectConfig.load(aio_dir)
        # Flag overrides (US5 — T058)
        if theme:
            object.__setattr__(cfg, "theme", theme)
        if agent:
            object.__setattr__(cfg, "agent", agent)
        _log.debug("Config loaded: agent=%s, theme=%s", cfg.agent, cfg.theme)
    except Exception as exc:
        _log.debug("Could not load project config: %s", exc)

    _log.info("build: not yet implemented (planned for M1)")
    _log.info("Command complete")
