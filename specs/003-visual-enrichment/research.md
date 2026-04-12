# Research: AIO Phase 2 — Visual Enrichment (M2.5)

**Phase 0 Output** | **Date**: 2026-04-12 | **Plan**: `specs/003-visual-enrichment/plan.md`

This document inherits all project-level research recorded in `specs/main/research.md` (M0) and the M1 decisions in `specs/002-core-layouts-theme-system/research.md`. Only decisions that are new or that override prior choices are recorded here.

---

## Decision Log

### 1. HTML Comment Metadata Parsing Strategy

**Decision:** Extend the existing slide parser (Step 1 of the build pipeline) to extract `<!-- @key: value -->` HTML comment tags from the markdown *body* of each slide and merge them into `SlideAST.metadata`. The YAML frontmatter path is unchanged.

**Rationale:**
The existing `parse_slides()` function already populates `SlideAST.metadata` from YAML frontmatter. The new inline syntax targets the *body* of a slide rather than its header block — allowing authors to place directives alongside the relevant content. Keeping both paths feeding into the same `metadata` dict means the rest of the pipeline (`analyze_slides`, `compose_slides`) needs no structural changes: it still calls `ast.metadata.get("icon")`, `ast.metadata.get("chart")`, etc.

A single compiled regex over the full slide body is sufficient:
```python
_META_TAG_RE = re.compile(r'<!--\s*@([\w-]+)\s*:\s*(.*?)\s*-->', re.DOTALL)
```
All matching tags are removed from the body before passing the remaining text to the markdown renderer (requirement: tags must not appear in output HTML). The key is lowercased to satisfy case-insensitivity.

YAML frontmatter retains priority: if a key appears in both frontmatter and in an HTML comment, the frontmatter value wins. This mirrors how `@layout` overrides worked in M1.

**Alternatives considered:**
- **Mistune plugin hook** — register a custom renderer or token to intercept HTML comments at the AST level. More powerful but adds complexity and couples the parser to mistune internals. The regex approach is self-contained and unit-testable.
- **Separate pre-parse pass** — strip `<!-- @... -->` tags in a dedicated function before passing the slide to mistune. This is effectively what we do, minus the overhead of a separate function call.

---

### 2. Icon Module Architecture

**Decision:** Keep the icon library at `src/aio/visuals/svg/icons.py` (already shipping 159 icons) and extend it in-place: add the remaining icons to `_ICON_PATHS`, expose `list_icons()` and `render_icon(name, size, color)` from the same module, and add a thin `aio icons` CLI subcommand at `src/aio/commands/icons.py`. No separate `src/aio/icons/` directory or `icons.json` file is created.

**Rationale:**
Creating a parallel `src/aio/icons/` directory would duplicate data (the paths are already in `icons.py`) and violate the "don't design for hypothetical future requirements" rule. The existing `render_icon()` function already covers the core contract. Adding `list_icons() → list[str]` and ensuring we have 200+ entries in `_ICON_PATHS` satisfies all spec requirements without architectural churn.

The `icons.json` file described in the spec is a discovery index for external tooling. Since AIO has no external tooling that consumes it, and the CLI command can read directly from `_ICON_PATHS`, the JSON file is deferred to M4 (if needed for the theme sync script).

**Icon count gap:** The current `_ICON_PATHS` has ~159 entries. Phase 2 requires ≥ 200. The implementation step will add ~41 icons from the same Lucide v0.462 source.

**Alternatives considered:**
- **Separate `icons.json` + SVG file tree** — mirrors the spec literally but doubles the packaging surface and adds file I/O on every `render_icon()` call. The in-memory dict approach is faster and simpler.
- **Download icons at build time from Lucide CDN** — violates Art. II (offline-first) and Art. VII (no network deps in core).

---

### 3. Chart Type Extension Strategy

**Decision:** Add three new chart types to `src/aio/visuals/dataviz/charts.py` as new classes inheriting `BaseChart`: `DonutChart`, `SparklineChart`, `TimelineChart`. Extend `render_chart()` factory to dispatch them. Do not rename or break the existing five types (Bar, Line, Pie, Scatter, Heatmap).

**Naming note:** The spec uses `@chart: bar` and `@chart: donut`. The existing metadata syntax in M1/M2 used `@chart-type: bar`. Phase 2 introduces a new, cleaner syntax via HTML comments (`<!-- @chart: bar -->`). The metadata key stored in `SlideAST.metadata` will be normalized to `"chart"` (without the `type` suffix) when parsed from HTML comments, while the old `"chart-type"` key from YAML frontmatter remains supported for backwards compatibility.

**Donut vs Pie:** `PieChart` renders filled sectors with no centre hole. `DonutChart` adds a configurable `inner_radius` ratio (default 0.55). Both live in `charts.py`; `DonutChart` can delegate sector math to `PieChart` and override only the centre cutout.

**Sparkline:** A minimal 200 × height SVG with a filled polyline. No axes, no labels. Accepts a flat list of numbers (not key-value pairs).

**Timeline:** A vertical SVG with equidistant milestone rows: dot → connector line → date label → event label. Horizontal orientation is a CSS media-query concern, not a Python SVG concern — the SVG uses `viewBox` without fixed pixel units so CSS `width: 100%` makes it responsive.

**Alternatives considered:**
- **Separate `dataviz_v2.py`** — unnecessary versioning overhead for an additive change.
- **Use a third-party library (cairosvg, matplotlib)** — violates Art. VII (no heavy deps in core).

---

### 4. CSS Decoration Generation Strategy

**Decision:** CSS decorations are generated at *theme load time* from section 12 of `DESIGN.md` and appended as a `<style>` block in the rendered HTML document (Step 4, `render_document`). They are NOT stored as separate `.css` files or injected into `layout.css`.

**Rationale:**
AIO's build pipeline already inlines all CSS from the active theme (theme.css + layout.css) into the output HTML. Adding decoration CSS as a generated string appended to the existing inline `<style>` block is the least-invasive integration point and preserves the Art. II (offline) guarantee without new I/O.

The DESIGN.md parser (`src/aio/themes/parser.py`) currently handles 11 sections. Section 12 "Decorations" is additive — the parser will return `None` if the section is absent (no error), and the decoration generator will emit fallback CSS in that case.

Generated CSS class naming: `.decoration-{type}-{variant}` (e.g., `.decoration-gradient-primary`). Each slide `<section>` element receives the class when `@decoration` is set.

Default fallback decorations (when section 12 is absent):
```css
.decoration-gradient-primary { background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%); }
.decoration-border-primary   { border-left: 4px solid var(--color-primary); }
.decoration-shadow-primary   { box-shadow: 0 8px 32px rgba(0,0,0,.18); }
.decoration-glow-primary     { text-shadow: 0 0 24px var(--color-accent); }
```

**Alternatives considered:**
- **Write decoration CSS to `layout.css` at import time** — durable but requires re-importing themes when section 12 changes, and bleeds decoration state into the per-theme files.
- **Inline `style=` attributes on `<section>`** — acceptable for gradients but does not support pseudo-elements (::before for accent lines), glow effects (text-shadow must cascade), or responsive overrides.

---

### 5. Image Enrichment Integration

**Decision:** `src/aio/_enrich.py` is a lazily-imported module containing the `EnrichEngine` class. It is imported only when `--enrich` is passed to `aio build`. The `--enrich` flag is added to the `build` command via Typer. The Enrich step runs as a 4.5th step between `render_document` (step 4) and `inline_assets` (step 5), post-processing the rendered HTML string to replace placeholder markers with base64-inlined images.

**HTTP client decision:** `urllib.request` from the stdlib is used rather than `httpx` or `requests`. This avoids adding a new dependency in violation of Art. VII. The Pollinations.ai endpoint is a simple GET request — no auth headers, no streaming, no session management — so `urllib.request.urlopen(url, timeout=30)` is sufficient.

**URL safety:** The Pollinations.ai URL is constructed from a server-side template with only the prompt, seed, and width/height as parameters. The prompt is URL-encoded via `urllib.parse.quote()`. No user-supplied URLs are passed directly to `urlopen()`.

**Seed derivation:**
```python
import hashlib
seed = int(hashlib.sha256(f"{deck_title}:{slide_index}".encode()).hexdigest()[:8], 16) % (2**31)
```
This is deterministic and bounded to Pollinations' expected seed range.

**Placeholder SVG:** When the API fails, a grey `<rect>` with an `<text>` label is inlined instead. This is < 200 bytes and maintains the Art. II guarantee.

**Prompt inference:** `title + " " + body[:80]` stripped of HTML tags and truncated to 100 chars. If the result is < 3 chars, falls back to `"Abstract presentation slide"`.

**Alternatives considered:**
- **`httpx`** — async-capable but requires an additional dependency. The build step is synchronous; no async benefit.
- **`requests`** — same issue: an extra dependency for a trivial GET.
- **Parallelize image generation** — `ThreadPoolExecutor` could speed up multi-slide enrichment but complicates error handling and progress reporting. Deferred to M3 if needed.

---

### 6. Build Pipeline Step Numbering

**Decision:** The pipeline is labelled as 6 steps internally when `--enrich` is active, and 5 steps otherwise. The step numbers reported in logs are dynamic: `Step 4.5/6: ENRICH` appears only when the flag is set. The `BuildResult` dataclass gains an `enrich_used: bool` field (already present in the codebase) and a `steps_total: int` field.

**`--dry-run` flag:** Typer `Option(False)` added to `aio build`. When set, `build.py` prints the step names to stderr and returns immediately without writing output.

**Alternatives considered:**
- **Always 6 steps, Enrich is a no-op when --enrich is absent** — simpler counting but misleading log output ("Step 4.5/6: ENRICH (skipped)") adds noise for the common case.
