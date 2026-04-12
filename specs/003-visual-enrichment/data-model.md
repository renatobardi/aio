# Data Model: AIO Phase 2 — Visual Enrichment (M2.5)

**Phase 1 Output** | **Date**: 2026-04-12 | **Plan**: `specs/003-visual-enrichment/plan.md`

---

## Overview

Phase 2 extends the existing pipeline data model with three new concerns:

1. **Inline metadata parsing** — `<!-- @key: value -->` tags extracted from the slide body and merged into `SlideAST.metadata`.
2. **New chart types** — `DonutChart`, `SparklineChart`, `TimelineChart` added to the existing chart class hierarchy.
3. **Enrichment context** — per-slide image generation state threaded through the pipeline from Compose to Enrich.

All new entities follow the existing conventions: `@dataclass(frozen=True)` for value objects, absolute imports, and no relative imports.

---

## Modified Entities

### SlideAST (existing — `src/aio/composition/metadata.py`)

No new fields. The `metadata: dict[str, str]` field already exists and will carry the new inline metadata keys:

| New Key | Source | Consumed By |
|---------|--------|-------------|
| `"icon"` | `<!-- @icon: name -->` | `compose_slides()` |
| `"icon-size"` | `<!-- @icon-size: 64px -->` | `compose_slides()` |
| `"icon-color"` | `<!-- @icon-color: #hex -->` | `compose_slides()` |
| `"chart"` | `<!-- @chart: bar -->` | `compose_slides()` |
| `"data"` | `<!-- @data: Q1:50, Q2:75 -->` | `compose_slides()` |
| `"decoration"` | `<!-- @decoration: gradient -->` | `compose_slides()` |
| `"decoration-type"` | `<!-- @decoration-type: primary -->` | `compose_slides()` |
| `"image-prompt"` | `<!-- @image-prompt: ... -->` | `_enrich.py` |

Backwards-compatible: existing `"chart-type"` and `"chart-data"` keys (from YAML frontmatter) continue to work. When both `"chart"` (HTML comment) and `"chart-type"` (frontmatter) are present, the HTML comment key (`"chart"`) takes precedence.

---

### SlideRenderContext (existing — `src/aio/composition/metadata.py`)

Two new optional fields:

```python
@dataclass(frozen=True)
class SlideRenderContext:
    # ... existing fields unchanged ...
    
    # Phase 2 additions
    icon_name: str | None = None          # resolved icon name (post-fallback)
    icon_size: str = "48px"               # CSS size value
    icon_color: str | None = None         # CSS color; None → inherits theme var
    chart_svg: str | None = None          # pre-rendered SVG string (replaces chart_type/chart_data)
    decoration_class: str | None = None   # e.g. "decoration-gradient-primary"
    decoration_style: str | None = None   # inline style for the <section> element
    image_prompt: str | None = None       # raw prompt for enrichment (explicit or inferred)
```

**Validation rules:**
- `icon_size` must match `re.match(r'^\d+(\.\d+)?(px|rem|em|%)$', value)`. Invalid values fall back to `"48px"` with a warning.
- `decoration_class` must match `^decoration-[a-z]+-[a-z]+$`. Unrecognised decoration types use the default gradient.

---

### BuildResult (existing — `src/aio/composition/metadata.py`)

One new field:

```python
@dataclass
class BuildResult:
    # ... existing fields unchanged ...
    enrich_used: bool = False                             # already present
    steps_total: int = 5                                  # NEW: 5 without --enrich, 6 with
    enrich_contexts: list[EnrichContext] = field(default_factory=list)  # NEW: per-slide enrichment state
```

---

## New Entities

### InlineMetadata (new — `src/aio/composition/metadata.py`)

Value object returned by the inline metadata parser. Not persisted; used only during `parse_slides()`.

```python
@dataclass(frozen=True)
class InlineMetadata:
    key: str    # lowercase, e.g. "icon"
    value: str  # stripped value string, e.g. "brain"
    line: int   # 1-based line number in the original slide source (for error messages)
```

| Field | Type | Validation |
|-------|------|------------|
| `key` | `str` | Non-empty; matches `^[\w-]+$`; lowercased |
| `value` | `str` | Non-empty after stripping; may contain special chars |
| `line` | `int` | ≥ 1 |

---

### DonutChart (new — `src/aio/visuals/dataviz/charts.py`)

Extends `PieChart` with a centre cutout.

```python
class DonutChart(BaseChart):
    inner_radius_ratio: float = 0.55   # ratio of outer radius; creates the hole
    center_label: str | None = None    # text rendered in the centre (e.g. "4 Languages")
```

**Rendering contract:**
- Accepts `ChartData` with `chart_type = "donut"`.
- Sectors are identical to `PieChart` but clipped by an inner white circle at `inner_radius_ratio × outer_radius`.
- `center_label` defaults to `f"{len(data.series)} items"` if not supplied via `@title` metadata.
- Output: valid SVG, ≤ 5 KB, no external resources.

**Validation rules:**
- `inner_radius_ratio` must be in `(0.0, 0.95)`. Values outside this range are clamped with a warning.
- Empty `ChartData` (zero series) renders a grey placeholder ring with the text "No data".

---

### SparklineChart (new — `src/aio/visuals/dataviz/charts.py`)

Minimal inline chart for embedding in running text.

```python
class SparklineChart(BaseChart):
    width: int = 200    # SVG viewport width in px
    height: int = 40    # SVG viewport height in px; @height metadata overrides this
    color: str = "var(--color-primary)"   # stroke and fill color
    fill_opacity: float = 0.15            # area fill transparency
```

**Rendering contract:**
- Accepts a flat numeric list from `ChartData` (single series, no labels).
- Renders a `<polyline>` connecting normalized data points plus a `<path>` for the filled area below the line.
- No axes, no tick marks, no legend — visual communication only.
- The `<svg>` uses `display: inline-block; vertical-align: middle` via a `style` attribute for inline placement.
- Output: valid SVG, ≤ 2 KB.

**Validation rules:**
- Fewer than 2 data points → warning logged; renders an empty SVG placeholder.
- All-identical values → horizontal line at mid-height.

---

### TimelineChart (new — `src/aio/visuals/dataviz/charts.py`)

Vertical milestone timeline.

```python
class TimelineChart(BaseChart):
    dot_radius: int = 6            # milestone dot radius
    connector_width: int = 2       # vertical connector line width
    date_color: str = "var(--color-neutral-500)"  # muted date label color
    label_color: str = "var(--color-text)"         # primary event label color
```

**Rendering contract:**
- Accepts `ChartData` where each series has `label = date_string` and `values[0]` is treated as the event name (string stored in a custom `events: list[tuple[str, str]]` parsed from `@data`).
- Data format: multi-line `@data` with `date: event label` pairs, one per line.
- Renders top-to-bottom: dot → vertical connector → `date` text left-aligned → `event` text right-aligned.
- `viewBox` uses proportional units; CSS `width: 100%` makes it scale with the slide.
- Output: valid SVG, ≤ 5 KB for ≤ 20 events.

**Validation rules:**
- More than 50 events → warning logged; only first 50 rendered with a trailing "…N more" label.
- Empty or malformed date string → event is rendered without a date; warning logged.

---

### DecorationSpec (new — `src/aio/themes/parser.py`)

Parsed decoration entry from DESIGN.md section 12.

```python
@dataclass(frozen=True)
class DecorationSpec:
    name: str           # slug, e.g. "gradient-primary"
    css_class: str      # e.g. "decoration-gradient-primary"
    css_value: str      # raw CSS property value, e.g. "linear-gradient(135deg, #635BFF 0%, #00D084 100%)"
    css_property: str   # e.g. "background", "box-shadow", "border-left", "text-shadow"
    responsive_value: str | None = None   # simplified value for @media (max-width: 768px); None = keep same
```

| Field | Validation |
|-------|------------|
| `name` | Non-empty; matches `^[a-z][a-z0-9-]*$` |
| `css_class` | Always `"decoration-" + name` |
| `css_value` | Non-empty; validated loosely (not via cssutils unless `[enrich]` installed) |
| `css_property` | One of: `"background"`, `"box-shadow"`, `"border-left"`, `"text-shadow"`, `"border-top"` |

---

### EnrichContext (new — `src/aio/_enrich.py`)

Per-slide enrichment state. Thread through pipeline from Compose to Enrich step.

```python
@dataclass
class EnrichContext:
    slide_index: int             # 0-based
    prompt: str                  # explicit or inferred; max 100 chars
    seed: int                    # deterministic sha256-derived seed
    image_bytes: bytes | None = None     # set by EnrichEngine; None until enriched
    is_placeholder: bool = False         # True when API failed or was skipped
    error_message: str | None = None     # set on API failure
```

**Lifecycle:**
1. Created during `compose_slides()` for each slide that has an `image_prompt` in its render context.
2. Passed to `EnrichEngine.enrich_all()` during step 4.5.
3. After enrichment: `image_bytes` is set (or `is_placeholder=True` on failure).
4. `render_document()` uses `image_bytes` (base64-encoded) or a placeholder SVG string to fill the `<img>` tag.

**Validation rules:**
- `prompt` truncated to 100 chars before API call.
- `seed` bounded to `[0, 2^31 - 1]`.
- `image_bytes` must be valid JPEG if not None (validated via `image_bytes[:3] == b'\xff\xd8\xff'`).

---

## Data Flow Diagram

```
Markdown source
      │
      ▼ parse_slides()  [Step 1]
      │  ┌─────────────────────────────────────┐
      │  │ Extract <!-- @key: value --> tags    │
      │  │ Merge into SlideAST.metadata         │
      │  │ Remove comment tags from body        │
      │  └─────────────────────────────────────┘
      ▼ SlideAST[]
      │
      ▼ analyze_slides()  [Step 2]
      │  Layout inference unchanged
      ▼ SlideRenderContext[]   ← now carries icon_name, chart_svg stub, decoration_class, image_prompt
      │
      ▼ compose_slides()  [Step 3]  ← EXPANDED
      │  ┌─────────────────────────────────────────────────┐
      │  │ For each slide:                                  │
      │  │   resolve_icon()    → chart_svg or icon HTML     │
      │  │   render_chart()    → SVG string                 │
      │  │   resolve_decoration() → CSS class + style       │
      │  │   build EnrichContext (if image_prompt present)  │
      │  └─────────────────────────────────────────────────┘
      ▼ ComposedSlide[]
      │
      ▼ render_document()  [Step 4]
      │  Assemble HTML; decoration CSS appended to <style>
      ▼ html: str
      │
      ▼ enrich_document()  [Step 4.5 — only if --enrich]
      │  ┌─────────────────────────────────────┐
      │  │ EnrichEngine.enrich_all(contexts)   │
      │  │ → replaces placeholder markers with │
      │  │   base64 JPEG or placeholder SVG    │
      │  └─────────────────────────────────────┘
      ▼ html: str (enriched)
      │
      ▼ inline_assets()  [Step 5]
      │  Verify zero external URLs (exit 3 on failure)
      ▼ final HTML file
```
