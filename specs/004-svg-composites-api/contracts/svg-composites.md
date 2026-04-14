# Interface Contract: SVG Composites Engine

**Feature**: Phase 2.5 — Visual Richness  
**Created**: 2026-04-13  
**Location**: `src/aio/visuals/svg/composites.py`

---

## SVGComposer Interface

### Method: compose()

**Signature**:
```python
def compose(
    composite_type: str,
    theme: ThemeRecord,
    dimensions: tuple[int, int] = (1920, 1080),
    seed: int | None = None
) -> str
```

**Purpose**: Generate a deterministic SVG composition matching theme palette and visual preferences.

**Parameters**:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `composite_type` | str | ✓ | — | One of 8: hero-background, feature-illustration, stat-decoration, section-divider, abstract-art, process-steps, comparison-split, grid-showcase |
| `theme` | ThemeRecord | ✓ | — | Theme object with palette and visual_config (from DESIGN.md section 10) |
| `dimensions` | tuple[int, int] | | (1920, 1080) | Output dimensions (width, height) in pixels |
| `seed` | int | | None | Optional seed for deterministic randomness; if None, derived from hash(theme_id + type) |

**Returns**: `str` — Valid W3C SVG as string (`<svg>...</svg>` element)

**Throws**:
- `VisualsException`: If SVG generation fails; automatically returns minimum valid SVG fallback
- `ValueError`: If `composite_type` not in supported 8 types
- `TypeError`: If theme is None or palette missing

**Behavior**:

1. Extract 2–3 colors from `theme.palette` (primary, secondary, accent)
2. Read `theme.visual_config` (from DESIGN.md section 10)
   - If absent: use defaults (tech/geometric/sharp/static)
3. Select composition strategy based on `composite_type`:
   - **hero-background**: Wave + gradient (large, abstract)
   - **feature-illustration**: 2-column split with icons
   - **stat-decoration**: Grid + circles + numbers
   - **section-divider**: Horizontal stripe pattern
   - **abstract-art**: Generative pattern (geo/organic based on config)
   - **process-steps**: Numbered boxes + flow arrows
   - **comparison-split**: Side-by-side columns
   - **grid-showcase**: Regular grid of cells
4. Apply style heuristics:
   - `visual_style_preference="tech"` → straight lines, grid, ≤45° angles
   - `visual_style_preference="organic"` → curves, waves, soft edges
   - `visual_style_preference="minimal"` → sparse, high contrast
   - `visual_style_preference="geometric"` → structured, symmetrical
5. Render SVG primitives (rect, circle, path, gradient, wave, grid)
6. Validate W3C compliance (no `<script>` tags)
7. Return inline SVG string

**Performance**:
- Target: <50ms (P95) across all 8 types on all 64 themes
- Measured as: time from compose() call to return

**Example**:
```python
svg = SVGComposer.compose(
    "hero-background",
    theme=theme_linear,
    dimensions=(1920, 1080),
    seed=12345
)
# Returns:
# <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080">
#   <defs>
#     <linearGradient id="grad1">...</linearGradient>
#   </defs>
#   <rect fill="url(#grad1)" width="1920" height="1080"/>
#   <path d="M 0,540 Q 480,450 960,540 T 1920,540" stroke="#0EA5E9" .../>
# </svg>
```

**Contract Tests** (`tests/integration/visuals/test_svg_composites_types.py`):
```python
def test_all_8_types_render_on_all_themes():
    """All 8 types must render without error on 100% of 64 themes."""
    # Arrange
    types = [
        "hero-background", "feature-illustration", "stat-decoration",
        "section-divider", "abstract-art", "process-steps",
        "comparison-split", "grid-showcase"
    ]
    
    # Act & Assert
    for theme in load_all_themes():  # 64 themes
        for comp_type in types:
            svg = SVGComposer.compose(comp_type, theme)
            assert "<svg" in svg
            assert "</svg>" in svg
            assert validate_w3c_svg(svg)
            assert len(gzip.compress(svg.encode())) <= 20_000  # ≤20 KB

def test_deterministic_generation():
    """Same seed + type + theme → same SVG."""
    svg1 = SVGComposer.compose("hero-background", theme, seed=12345)
    svg2 = SVGComposer.compose("hero-background", theme, seed=12345)
    assert svg1 == svg2

def test_fallback_on_error():
    """If generation fails, return minimum valid SVG (not exception)."""
    # (Test with corrupted theme or invalid params)
    svg = SVGComposer.compose("hero-background", None)  # Should not crash
    assert "<svg" in svg
    assert validate_w3c_svg(svg)
```

---

## SVG Primitive Functions

### rect(x, y, w, h, fill, opacity, stroke, stroke_width)
```python
def rect(x: int, y: int, w: int, h: int,
         fill: str, opacity: float = 1.0,
         stroke: str | None = None, stroke_width: int = 0) -> str
```
Returns: `<rect x="..." y="..." width="..." height="..." fill="..." .../>`

### circle(cx, cy, r, fill, opacity, stroke, stroke_width)
```python
def circle(cx: int, cy: int, r: int,
           fill: str, opacity: float = 1.0,
           stroke: str | None = None, stroke_width: int = 0) -> str
```
Returns: `<circle cx="..." cy="..." r="..." fill="..." .../>`

### path(d, stroke, fill, stroke_width, opacity)
```python
def path(d: str, stroke: str | None = None, fill: str | None = None,
         stroke_width: int = 1, opacity: float = 1.0) -> str
```
Returns: `<path d="..." stroke="..." fill="..." .../>`

### gradient(grad_type, stops, angle)
```python
def gradient(grad_type: Literal["linear", "radial"],
             stops: list[tuple[float, str]],  # [(offset_0to1, color_hex), ...]
             angle: int = 0) -> str  # angle in degrees (0-360)
```
Returns: `<defs><linearGradient id="gradN">...</linearGradient></defs>`

### wave(width, height, amplitude, frequency, color, opacity)
```python
def wave(width: int, height: int,
         amplitude: int = 50, frequency: float = 0.01,
         color: str = "#0EA5E9", opacity: float = 0.3) -> str
```
Returns: `<path d="M 0,H Q x1,y1 x2,y2 ... Z" .../>`

### grid(width, height, cell_size, color, opacity, stroke_width)
```python
def grid(width: int, height: int, cell_size: int = 50,
         color: str = "#000000", opacity: float = 0.1,
         stroke_width: int = 1) -> str
```
Returns: Multiple `<line>` elements forming grid

---

## Errors & Fallback Behavior

**Exception Hierarchy**:
- `VisualsException` (base)
  - `SVGRenderError` (primitive rendering failed)
  - `SVGValidationError` (output not W3C valid)
  - `ThemeDataError` (theme palette/config malformed)

**Fallback Strategy**:
```
try:
    svg = SVGComposer.compose(type, theme, dimensions, seed)
except VisualsException as e:
    logger.warning(f"SVG composition failed: {e}")
    svg = FALLBACK_SVG  # Minimum valid SVG with solid fill + gradient
return svg  # Never raise; always return valid SVG
```

**Fallback SVG**:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080">
  <defs>
    <linearGradient id="fallback" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#F3F4F6;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#E5E7EB;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1920" height="1080" fill="url(#fallback)"/>
</svg>
```

---

## Integration Points

### 1. Composition Pipeline Integration
**File**: `src/aio/composition/engine.py`  
**Step 2** (analyze_slides):
```python
for slide in slide_asts:
    context = CompositionEngine.infer_layout(slide)
    # NEW: Add SVG composite
    if slide.type in ENRICHABLE_TYPES:
        svg = SVGComposer.compose(
            composite_type=infer_composite_type(slide),
            theme=theme,
            dimensions=(1920, 1080)
        )
        context.svg_composite = svg
    render_contexts.append(context)
```

### 2. Theme Loading Integration
**File**: `src/aio/themes/loader.py`  
**On theme load**:
```python
theme = load_theme(theme_id)
# Extract visual config from DESIGN.md section 10
if "visual_config" not in theme.metadata:
    theme.metadata["visual_config"] = auto_generate_defaults(theme)
SVGComposer.compose(..., theme=theme)  # Will use theme.metadata["visual_config"]
```

### 3. HTML Rendering Integration
**File**: `src/aio/composition/templates/base.j2`  
**In slide template**:
```jinja2
{% if slide.svg_composite %}
  <div class="slide-background">
    {{ slide.svg_composite | safe }}
  </div>
{% endif %}
```

---

## Success Criteria

| SC ID | Criterion | Test |
|-------|-----------|------|
| SC-401 | All 8 types render on 100% of 64 themes (0 failures) | `pytest tests/integration/visuals/test_svg_composites_types.py::test_all_8_types_render_on_all_themes` |
| SC-402 | Output is W3C valid SVG | `xmllint --noout output.svg` in each test |
| SC-403 | Avg ≤18 KB, P95 ≤25 KB (gzip) | Collect gzip sizes; assert stats |
| SC-404 | Colors from palette with 100% precision | Hex string match in generated SVG |
| SC-405 | Visual diffs <1% across themes | SVG→PNG pixel comparison |
| SC-406 | <50ms P95 performance | Profile on all 8 types × 64 themes |

---
