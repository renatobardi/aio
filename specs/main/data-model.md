# Data Model: AIO — AI-Native Presentation Generator

**Phase 1 Output** | **Date**: 2026-04-11 | **Plan**: `specs/main/plan.md`

---

## Core Entities

### SlideAST

Internal representation of a parsed slide. Produced by Step 1 (Parse) of the build pipeline.

| Field | Type | Description |
|-------|------|-------------|
| `index` | `int` | Zero-based slide position in deck |
| `frontmatter` | `dict[str, Any]` | Parsed YAML frontmatter via `yaml.safe_load()` |
| `title` | `str \| None` | First `# heading` extracted from body |
| `body_tokens` | `list[Token]` | mistune AST tokens for slide body |
| `raw_markdown` | `str` | Original markdown source (for debugging) |
| `layout_hint` | `str \| None` | `frontmatter.get('layout')` — manual override |

**Validation rules:**
- `frontmatter` MUST be parsed with `yaml.safe_load()` — never `yaml.load()`
- `body_tokens` is never None; empty list for title-only slides

---

### SlideMetadata

Rich metadata per slide. Populated during Step 2 (Resolve) and extended in M3.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `layout` | `str` | (inferred) | Selected layout class name |
| `timing` | `int \| None` | None | Slide duration in seconds |
| `transition` | `str` | `"slide"` | Reveal.js transition name |
| `transition_speed` | `str` | `"default"` | `"fast"`, `"slow"`, `"default"` |
| `notes` | `str \| None` | None | Speaker notes content |
| `auto_animate` | `bool` | False | Reveal.js auto-animate flag |
| `background_color` | `str \| None` | None | Slide-level background override |
| `visibility` | `str` | `"visible"` | `"hidden"` skips slide in output |

---

### DeckMetadata

Global metadata for the presentation. Populated from deck-level YAML frontmatter (first slide or
dedicated `---deck---` block).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `title` | `str` | `"Untitled"` | Presentation title |
| `author` | `str \| None` | None | Author name |
| `theme_id` | `str` | `"minimal"` | Theme ID from registry |
| `agent` | `str` | `"claude"` | Default AI agent |
| `agent_version` | `str` | `"v1"` | Agent prompt version |
| `created_at` | `str` | ISO 8601 | Build timestamp |
| `reveal_config` | `dict` | `{}` | Passed directly to `Reveal.initialize()` |

---

### ThemeRecord

One entry in `src/aio/themes/registry.json`.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Slug (e.g., `"minimal"`) — unique |
| `name` | `str` | Human display name |
| `description` | `str` | One-line summary |
| `tags` | `list[str]` | e.g., `["dark", "minimal", "corporate"]` |
| `author` | `str` | Theme author |
| `source` | `str` | `"builtin"` or `"awesome-design-md"` |
| `path` | `str` | Relative path to theme dir |
| `created_at` | `str` | ISO 8601 |
| `updated_at` | `str` | ISO 8601 |

---

### ThemeAssets

In-memory representation of a loaded theme. Produced by `themes/loader.py`.

| Field | Type | Description |
|-------|------|-------------|
| `record` | `ThemeRecord` | Registry entry |
| `theme_css` | `str` | Contents of `theme.css` |
| `layout_css` | `str` | Contents of `layout.css` |
| `fonts_b64` | `dict[str, str]` | `{family: base64_woff2}` — inlined fonts |
| `design` | `DesignSpec` | Parsed DESIGN.md |

---

### DesignSpec

Parsed representation of a theme's `DESIGN.md`. 11 sections are required.

| Field | Type | Description |
|-------|------|-------------|
| `visual_theme` | `str` | Section 1 content |
| `color_palette` | `dict[str, str]` | `{role: hex}` — primary, secondary, accent, danger |
| `typography` | `dict[str, Any]` | Fonts, sizes, weights, line-heights |
| `components` | `dict[str, str]` | CSS specs for buttons, badges, cards, callouts, code |
| `layout_system` | `dict[str, Any]` | Grid, spacing scale, breakpoints |
| `depth_shadows` | `dict[str, str]` | Elevation 0–4 shadow CSS |
| `dos_donts` | `dict[str, list[str]]` | `{"do": [...], "dont": [...]}` |
| `responsive` | `str` | Mobile-first strategy description |
| `animations` | `dict[str, Any]` | Speeds, easing, trigger definitions |
| `accessibility` | `dict[str, Any]` | WCAG claims, contrast ratios, alt-text rules |
| `agent_snippet` | `str` | ~200-word prompt snippet for AI agents |

---

### ChartData

Input to the DataViz engine.

| Field | Type | Description |
|-------|------|-------------|
| `chart_type` | `str` | `"bar"`, `"line"`, `"pie"`, `"scatter"`, `"heatmap"` |
| `title` | `str \| None` | Chart title |
| `labels` | `list[str]` | X-axis or category labels |
| `series` | `list[Series]` | One or more data series |
| `x_label` | `str \| None` | X-axis label |
| `y_label` | `str \| None` | Y-axis label |
| `width` | `int` | SVG width in px (default: 800) |
| `height` | `int` | SVG height in px (default: 450) |

---

### Series

One data series within a `ChartData`.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Series label (for legend) |
| `values` | `list[float]` | Numeric data points |
| `color` | `str \| None` | Hex color override (theme color used if None) |

---

### EnrichRequest

Input to the enrichment pipeline.

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | `str` | Image generation prompt |
| `slide_index` | `int` | Which slide this image is for |
| `provider` | `str` | `"pollinations"`, `"dalle"`, `"midjourney"`, `"stable-diffusion"` |
| `width` | `int` | Target width (default: 1920) |
| `height` | `int` | Target height (default: 1080) |

---

### EnrichResult

Output from the enrichment pipeline.

| Field | Type | Description |
|-------|------|-------------|
| `slide_index` | `int` | Corresponding slide |
| `image_b64` | `str \| None` | Base64-encoded image (None if failed) |
| `svg_fallback` | `str \| None` | SVG placeholder (set when image_b64 is None) |
| `provider_used` | `str` | Actual provider that served the image |
| `duration_ms` | `int` | Round-trip time in milliseconds |

---

### AgentTemplate

In-memory representation of a vendored agent prompt.

| Field | Type | Description |
|-------|------|-------------|
| `agent` | `str` | e.g., `"claude"` |
| `version` | `str` | e.g., `"v1"` |
| `system` | `str` | Contents of `SYSTEM.md` |
| `init_phase` | `str` | Contents of `INIT_PHASE.md` |
| `composition_phase` | `str` | Contents of `COMPOSITION_PHASE.md` |
| `enrich_phase` | `str` | Contents of `ENRICH_PHASE.md` |
| `refinement_phase` | `str` | Contents of `REFINEMENT_PHASE.md` |

---

## State Transitions

### Build Pipeline States

```
INPUT (raw .md file)
    │
    ▼ Pipeline.parse()
PARSED (SlideAST list + DeckMetadata)
    │
    ▼ Pipeline.resolve()
RESOLVED (SlideAST + SlideMetadata + ThemeAssets)
    │
    ▼ Pipeline.render()
RENDERED (HTML fragments per slide, inline SVG charts)
    │
    ▼ Pipeline.inline()
OUTPUT (single .html file, all assets inlined, external URL check passed)
```

### Enrich States

```
PENDING → IN_FLIGHT (async httpx call to provider)
         → SUCCESS (image_b64 set) → EMBEDDED (base64 in HTML)
         → FAILED  (svg_fallback set) → EMBEDDED (SVG placeholder in HTML)
```

---

## File System Layout

### Per-project (`.aio/`)

```
.aio/
├── meta.json              # DeckMetadata (JSON)
├── config.yaml            # User prefs (default agent, provider, theme)
└── themes/
    └── registry.json      # Selected theme only (subset of global registry)
```

### User home (`~/.aio/`)

```
~/.aio/
├── logs/
│   └── aio.log            # Rotating weekly log (stderr structured JSON)
└── cache/
    └── themes/            # Cached remote theme assets (optional)
```
