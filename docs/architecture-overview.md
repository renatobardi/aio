# AIO Architecture Overview

This document provides a high-level understanding of AIO's architecture, data flow, and key components.

---

## The Build Pipeline (5 Steps)

AIO transforms Markdown + YAML into a standalone HTML presentation through a **predictable 5-step pipeline**:

```
Input: slides.md (Markdown + YAML frontmatter)
  ↓
Step 1: Parse           → Raw slide data + metadata
  ↓
Step 2: Analyze         → Layout inference engine
  ↓
Step 3: Compose         → SVG charts + icons + layouts
  ↓
Step 4: Render          → Assemble Reveal.js HTML
  ↓
Step 5: Inline Assets   → Embed everything; verify no external URLs
  ↓
Output: out.html (single file, zero external deps)
```

### Step 1: Parse (`parse_slides`)

**Input**: `slides.md`  
**Output**: `SlideAST[]` (Abstract Syntax Tree)

```python
# Parses:
# - YAML frontmatter (title, subtitle, theme, etc.)
# - Markdown content (headings, paragraphs, code blocks)
# - Metadata comments (@chart-type, @icon-name, etc.)

SlideAST = {
    "title": "My Presentation",
    "theme": "linear",
    "slides": [
        {
            "heading": "Slide 1",
            "content": "...",
            "metadata": {...}
        }
    ]
}
```

**Code**: `src/aio/commands/build.py:parse_slides()`

---

### Step 2: Analyze (`analyze_slides`)

**Input**: `SlideAST[]`  
**Output**: `SlideRenderContext[]` (with inferred layouts)

```python
# CompositionEngine.infer_layout() examines:
# - Slide content (headings, # of paragraphs, images)
# - Metadata hints (@layout: hero, @layout: two-column)
# - Theme layout options

# Selects best layout from 8 options:
# - hero (full-screen title)
# - title (centered title + subtitle)
# - content (heading + paragraph)
# - two-column (two content areas)
# - comparison (left vs right)
# - gallery (image grid)
# - stats (numbers + icons)
# - split (image + text)

SlideRenderContext = {
    "slide": SlideAST,
    "layout": "hero",  # or "two-column", etc.
    "layout_vars": {...}
}
```

**Code**: `src/aio/composition/engine.py:CompositionEngine.infer_layout()`

---

### Step 3: Compose (`compose_slides`)

**Input**: `SlideRenderContext[]`  
**Output**: `ComposedSlide[]` (HTML fragments)

```python
# For each slide:
# 1. Load Jinja2 template matching the layout
#    (e.g., src/aio/layouts/hero.j2)
# 2. Process @chart-type metadata → generate SVG via visuals.dataviz
# 3. Process @icon-name metadata → render icons via visuals.svg.icons
# 4. Apply theme CSS variables (colors, fonts)
# 5. Render template → HTML fragment

ComposedSlide = {
    "html": "<div class='slide'>...</div>",
    "svg_charts": ["<svg>...</svg>"],
    "icons": ["<svg>...</svg>"]
}
```

**Code**: `src/aio/commands/build.py:compose_slides()`

**Subcomponents**:
- `src/aio/layouts/` — Jinja2 templates (one per layout type)
- `src/aio/visuals/dataviz/` — Chart generation (Bar, Line, Pie, etc.)
- `src/aio/visuals/svg/icons.py` — Icon renderer

---

### Step 4: Render (`render_document`)

**Input**: `ComposedSlide[]`  
**Output**: HTML string (complete document)

```python
# 1. Load Reveal.js 5.x from vendor
# 2. Assemble slides into Reveal.js structure
# 3. Inject CSS:
#    - theme.css (colors, typography)
#    - layout.css (layout-specific styles)
# 4. Inject JavaScript:
#    - Reveal.js UMD build
#    - SSE snippet (for serve hot-reload)
# 5. Return full HTML string

html = """
<html>
  <head>
    <style>/* theme + layout CSS inlined */</style>
  </head>
  <body>
    <div class="reveal">
      <div class="slides">
        <!-- composed slides here -->
      </div>
    </div>
    <script>/* Reveal.js + SSE inlined */</script>
  </body>
</html>
"""
```

**Code**: `src/aio/commands/build.py:render_document()`

---

### Step 5: Inline Assets (`inline_assets`)

**Input**: HTML string  
**Output**: Final HTML file (or SSE event stream in serve mode)

```python
# 1. Scan HTML for external URLs (href=, src=)
# 2. Verify NONE exist (Art. II compliance)
# 3. In serve mode: return SSE event stream
# 4. In build mode: write to disk

# Exit codes:
# 0 = success
# 1 = error (parse, composition, render)
# 2 = config error
# 3 = external URL found (Art. II violation)
```

**Code**: `src/aio/commands/build.py:inline_assets()`  
**Validator**: `src/aio/_validators.py:check_external_urls()`

---

## Module Organization

### Commands Layer (`src/aio/commands/`)

| Module | Purpose |
|--------|---------|
| `build.py` | 5-step pipeline orchestrator |
| `serve.py` | Starlette ASGI + watchdog + SSE hot-reload |
| `theme.py` | Theme list/info/validate/use |
| `init.py` | Scaffold `.aio/` project structure |
| `extract.py` | Scrape design sites → DESIGN.md |
| `commands.py` | List AI agent prompts |

### Composition Layer (`src/aio/composition/`)

| Module | Purpose |
|--------|---------|
| `engine.py` | `CompositionEngine` — layout inference |
| `layouts.py` | `LayoutType` enum (8 types) |
| `metadata.py` | Data classes (`SlideAST`, `SlideRenderContext`, etc.) |

### Visuals Layer (`src/aio/visuals/`)

| Submodule | Purpose |
|-----------|---------|
| `dataviz/charts.py` | 5 chart types (Bar, Line, Pie, Scatter, Heatmap) |
| `dataviz/data_parser.py` | CSV/JSON/dict → `ChartData` |
| `svg/icons.py` | 159 Lucide icons → SVG |
| `svg/composites.py` | Complex SVG (flowcharts, org charts, backgrounds) |

### Theme System (`src/aio/themes/`)

| Module | Purpose |
|--------|---------|
| `loader.py` | Load theme registry; parse `meta.json` |
| `parser.py` | Parse 11-section DESIGN.md |
| `validator.py` | Validate DESIGN.md + CSS |

### Utilities & Core (`src/aio/`)

| Module | Purpose |
|--------|---------|
| `_log.py` | Structured logging (stderr only; no stdout) |
| `_utils.py` | Jinja2 env builder, base64 encoding, etc. |
| `_validators.py` | YAML safe-load wrapper, URL checker |
| `exceptions.py` | Custom exception types |

---

## Key Data Structures

### SlideAST

```python
@dataclass
class SlideAST:
    heading: str
    content: str
    metadata: dict  # @chart-type, @icon-name, etc.
    frontmatter: dict  # Global: title, theme, subtitle
```

### SlideRenderContext

```python
@dataclass
class SlideRenderContext:
    slide: SlideAST
    layout: LayoutType  # One of 8 types
    layout_vars: dict  # Context for Jinja2 template
```

### ComposedSlide

```python
@dataclass
class ComposedSlide:
    html: str  # Rendered slide HTML
    layout: LayoutType
    metadata: dict
```

### ThemeRecord

```python
@dataclass
class ThemeRecord:
    id: str  # e.g., "linear", "stripe"
    meta: dict  # From meta.json
    design: dict  # Parsed DESIGN.md (11 sections)
    css: str  # theme.css + layout.css
```

---

## File Structure

```
aio/
├── src/aio/
│   ├── cli.py                    # Typer entry point
│   ├── commands/                 # Build, serve, theme, init, extract
│   ├── composition/              # Engine, layouts, metadata
│   ├── visuals/
│   │   ├── dataviz/             # Charts, data parser
│   │   └── svg/                 # Icons, composites
│   ├── themes/                   # Loader, parser, validator
│   ├── agents/                   # Prompt templates
│   ├── vendor/revealjs/          # Static Reveal.js 5.x
│   ├── layouts/                  # Jinja2 templates (*.j2)
│   ├── _log.py, _utils.py, _validators.py, exceptions.py
│   └── _enrich.py               # Image generation + caching
│
├── tests/
│   ├── unit/                     # Isolated function tests
│   ├── integration/              # Full pipeline tests
│   ├── fixtures/                 # Sample data, expected outputs
│   └── visual/                   # HTML snapshot tests
│
├── docs/                         # User guides, troubleshooting
├── specs/main/                   # Design docs, roadmap
├── .aio/themes/                  # 57+ theme directories
│
├── CLAUDE.md                     # AI assistant guidance
├── CONTRIBUTING.md               # Contributing workflow
└── README.md                     # Main user docs
```

---

## Design Principles (From Constitution)

### Article I — Python 3.12+ Only

- Modern syntax: walrus `:=`, `A | B` unions, `match/case`, `functools.cache`
- Type hints first-class: `@dataclass`, `TypedDict`, `Protocol`
- Exception: `cli.py` and `serve.py` cannot use `from __future__ import annotations` (breaks Typer)

### Article II — 100% Offline Output

- No external URLs in output HTML
- All CSS, JS, fonts, images are **inlined**
- Build **fails** (exit 3) if external URL detected
- Works offline on airplane, no internet required

### Article III — Visual Intelligence is Core

- Composition Engine is foundational (not optional)
- SVG composites, charts, and icons are central
- Every slide passes through layout inference

### Article VII — Minimal Dependencies

- Exactly 10 core deps (< 150 MB)
- Optional `[enrich]` for image gen (< 250 MB total)
- No Django, numpy, pandas, TensorFlow, ORM, or GraphQL

### Article VIII — Reveal.js Pinned to 5.x

- Static vendored build in `src/aio/vendor/revealjs/`
- Never upgrade to v6 without amendment
- Escape `</script>` → `<\/script>` in inlined JS

---

## How to Extend AIO

### Add a New Layout

1. Create `src/aio/layouts/my-layout.j2` (Jinja2 template)
2. Add layout type to `src/aio/composition/layouts.py:LayoutType`
3. Update inference logic in `src/aio/composition/engine.py:infer_layout()`
4. Write tests in `tests/integration/test_composition.py`

### Add a New Chart Type

1. Create class in `src/aio/visuals/dataviz/charts.py` extending `BaseChart`
2. Implement `render() → str` (returns SVG)
3. Register in chart factory
4. Write tests in `tests/unit/test_charts.py`

### Add a New Theme

1. Create directory: `src/aio/themes/my-theme/`
2. Add: `DESIGN.md` (11 sections), `theme.css`, `layout.css`, `meta.json`
3. Run: `aio theme validate my-theme`
4. Test: `aio build slides.md --theme my-theme`

---

## Performance Targets (from Constitution)

| Operation | Target |
|-----------|--------|
| Build — 30 slides | < 30s |
| Serve hot-reload | < 2s |
| Markdown parse — 100 slides | < 500ms |
| New code regression | No > 5% slowdown |

---

## Testing Strategy

- **Unit tests** (`tests/unit/`) — isolated functions, mocks OK
- **Integration tests** (`tests/integration/`) — full pipeline, real temp dirs, NO mocks for core pipeline
- **Visual tests** (`tests/visual/`) — HTML snapshots, SVG well-formedness
- **Fixtures** (`tests/fixtures/`) — shared sample slides, themes, API responses

**Coverage gate**: ≥ 20% (CI requirement)  
**Aspirational target**: 80% line / 75% branch

---

## Useful Commands for Exploration

```bash
# See what Composition Engine infers for a slide
aio build slides.md -v 2>&1 | grep "inferred layout"

# Profile build time
time aio build slides.md

# Check theme compliance
aio theme validate linear

# List all layouts available
grep "class.*Layout" src/aio/composition/layouts.py

# Find all Jinja2 templates
find src/aio/layouts -name "*.j2"

# Check SVG generation
python -c "from aio.visuals.svg.icons import render_icon; print(render_icon('check', '#000', 24))"
```

---

## Next Steps

- Read `src/aio/commands/build.py` to understand the 5-step pipeline
- Explore `src/aio/composition/engine.py` for layout inference logic
- Check `src/aio/layouts/` for Jinja2 template examples
- Review `specs/main/plan.md` for roadmap and design decisions
