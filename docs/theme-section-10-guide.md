# Theme Section 10 Authoring Guide

## Purpose

**DESIGN.md Section 10** defines the **Visual Style Preferences** that control how AIO automatically generates SVG compositions (backgrounds, illustrations, decorations) to match your theme's visual identity.

When this section is present and complete, all 8 SVG composition types adapt to your design system:
- **tech** → Grid patterns with straight lines (engineering, software, modern)
- **organic** → Curves and waves (nature, lifestyle, flowing)
- **minimal** → Sparse, high-contrast elements (clean, minimalist)
- **geometric** → Structured, symmetrical shapes (structured, sophisticated)

---

## Overview

Section 10 has **4 required fields**:

```yaml
# Section 10 title: "Visual Style Preference"
Visual Style Preference: tech
Pattern: grid
Curvature: sharp
Animation Preference: static
```

| Field | Values | Purpose |
|-------|--------|---------|
| **Visual Style Preference** | tech, organic, minimal, geometric | Overall aesthetic direction |
| **Pattern** | grid, dots, lines, mesh, noise, flowing | Surface decoration approach |
| **Curvature** | sharp, soft, mixed | Edge quality (straight vs. rounded) |
| **Animation Preference** | static, subtle, dynamic | Motion for future features |

---

## Authoring Section 10

### Step 1: Choose Your Visual Style Preference

This is the **primary axis** that controls SVG composition generation.

#### **tech** → Grid, Lines, Angles ≤45°

**Use for**: Software, SaaS, data, engineering, modern design

**Characteristics**:
- Grid-based layouts
- Straight lines, 90° angles
- Sharp, defined shapes
- High contrast
- Geometric precision

**Example themes**: Linear, Minimal Pro, Data Dark

```yaml
Visual Style Preference: tech
Pattern: grid  # Grid lines, geometric cells
Curvature: sharp  # 90° angles, no rounding
```

**SVG Output**:
```
Hero: Circles with grid overlay
Feature: Side-by-side rectangles
Stats: Numbered grid cells
```

---

#### **organic** → Curves, Waves, Flowing

**Use for**: Nature, lifestyle, wellness, creative, flowing

**Characteristics**:
- Curved paths, bezier curves
- Wave patterns, flowing shapes
- Soft edges, rounded corners
- Natural, smooth transitions
- Hand-drawn feeling

**Example themes**: Dribble, Nature, Creative

```yaml
Visual Style Preference: organic
Pattern: flowing  # Waves, organic shapes
Curvature: soft  # Rounded, no sharp angles
```

**SVG Output**:
```
Hero: Large ellipse with wave overlay
Feature: Soft-edged organic shapes
Stats: Rounded circle clusters
```

---

#### **minimal** → Sparse, High-Contrast

**Use for**: Minimalist, startup, elegant, premium

**Characteristics**:
- Few elements, plenty of whitespace
- High contrast color combinations
- Intentional, purposeful placement
- Reduced visual noise
- Premium feel

**Example themes**: Minimal, Zen, Premium

```yaml
Visual Style Preference: minimal
Pattern: dots  # Strategic dot placement
Curvature: sharp  # Clean lines
```

**SVG Output**:
```
Hero: 4 strategic dots in corners
Feature: Minimal separated elements
Stats: Simple circle accents
```

---

#### **geometric** → Structured, Symmetrical

**Use for**: Corporate, structured, mathematical, symmetric

**Characteristics**:
- Regular shapes, repetition
- Symmetrical layouts
- Mathematical precision
- Structured composition
- Formal, professional

**Example themes**: Corporate, Finance, Academic

```yaml
Visual Style Preference: geometric
Pattern: mesh  # Grid/mesh overlay
Curvature: sharp  # Clean geometric forms
```

**SVG Output**:
```
Hero: Perfect circles arranged symmetrically
Feature: Rectangles in structured layout
Stats: Regular polygon grid
```

---

### Step 2: Choose Your Pattern

Pattern refines **how** the composition is decorated within the visual style.

| Pattern | Pairs With | Appearance |
|---------|-----------|-----------|
| **grid** | tech, geometric | Regular grid lines, cells, graph paper |
| **dots** | minimal, tech | Scattered or regular dot placement |
| **lines** | tech, organic | Horizontal, vertical, or flowing lines |
| **mesh** | geometric, tech | Triangular or mesh overlay pattern |
| **noise** | organic, minimal | Grainy, textured appearance |
| **flowing** | organic | Wave, curve, flow patterns |

**Decision Matrix**:

```
Tech (prefer):
  - grid: Very structured (data, software)
  - dots: Minimal structure (modern SaaS)
  - lines: Linear, directional (flow, process)

Organic (prefer):
  - flowing: Waves, natural curves
  - noise: Texture, organic feel
  - lines: Flowing line patterns (not straight)

Minimal (prefer):
  - dots: Strategic placement
  - noise: Subtle texture
  - lines: Minimal line accents

Geometric (prefer):
  - mesh: Triangles, lattice
  - grid: Regular cells
  - dots: Symmetrical arrangement
```

**Example combinations**:
```yaml
# Tech + Grid = Engineering feel
Visual Style Preference: tech
Pattern: grid

# Organic + Flowing = Nature/lifestyle feel
Visual Style Preference: organic
Pattern: flowing

# Minimal + Dots = Clean, strategic
Visual Style Preference: minimal
Pattern: dots

# Geometric + Mesh = Structured, mathematical
Visual Style Preference: geometric
Pattern: mesh
```

---

### Step 3: Choose Your Curvature

Curvature defines **edge quality**: are lines straight or rounded?

| Value | Meaning | Pairs Well With |
|-------|---------|-----------------|
| **sharp** | 90° angles, no rounding | tech, geometric, minimal |
| **soft** | Rounded corners, flowing | organic, minimal |
| **mixed** | Some sharp, some soft | Any style (balanced) |

**Decision**:

```
sharp:
  - Use with tech, geometric, minimal
  - Creates precision, modern feel
  - Grid, rectangles, polygons
  - Example: Corporate, software

soft:
  - Use with organic, minimal
  - Friendly, approachable feel
  - Curves, ellipses, rounded shapes
  - Example: Lifestyle, startup

mixed:
  - Balanced, versatile
  - Combines hard and soft elements
  - Works with any visual style
  - Example: Creative, experimental
```

**Example combinations**:
```yaml
# Tech + Sharp = Maximum precision
Visual Style Preference: tech
Curvature: sharp

# Organic + Soft = Maximum friendliness
Visual Style Preference: organic
Curvature: soft

# Geometric + Mixed = Balanced structure
Visual Style Preference: geometric
Curvature: mixed
```

---

### Step 4: Choose Animation Preference

Animation Preference is **future-facing**; currently all SVGs are static.

| Value | Purpose | Future Use |
|-------|---------|-----------|
| **static** | No animation | Default; SVG is static |
| **subtle** | Gentle motion | Future: Fade, gentle pulse |
| **dynamic** | Obvious motion | Future: Animations, transitions |

**Recommendation**: Choose based on your theme's energy level.

```yaml
# Corporate, professional
Animation Preference: static

# Startup, modern
Animation Preference: subtle

# Creative, energetic
Animation Preference: dynamic
```

---

## Complete Examples

### Example 1: Tech Startup (Modern SaaS)

```markdown
## 10. Visual Style Preference

A modern, tech-forward aesthetic with clean lines and structured layouts.

```yaml
visual_style_preference: tech
pattern: grid
curvature: sharp
animation_preference: subtle
```

**Rationale**:
- **tech**: Aligns with software/SaaS industry
- **grid**: Represents data, structure, and precision
- **sharp**: Clean, modern, professional
- **subtle**: Inviting but professional energy
```

**SVG Result**:
- Hero backgrounds: Grid patterns with geometric overlays
- Features: Side-by-side columns with grid guides
- Stats: Numbered grid cells with data visualization feel
- Minimal curves; primarily straight lines and 90° angles

---

### Example 2: Wellness & Lifestyle Brand

```markdown
## 10. Visual Style Preference

Organic, flowing aesthetic celebrating natural beauty and human connection.

```yaml
visual_style_preference: organic
pattern: flowing
curvature: soft
animation_preference: dynamic
```

**Rationale**:
- **organic**: Mirrors nature, wellness, lifestyle focus
- **flowing**: Wave and curve patterns evoke movement and flow
- **soft**: Friendly, approachable, warm feeling
- **dynamic**: Energetic, modern wellness brand

```

**SVG Result**:
- Hero backgrounds: Wave patterns, soft gradients
- Features: Flowing curves, organic shapes, soft edges
- Stats: Curved circles, flowing line accents
- All edges rounded; no sharp angles

---

### Example 3: Minimalist Design Studio

```markdown
## 10. Visual Style Preference

Intentional minimalism with strategic use of whitespace and high contrast.

```yaml
visual_style_preference: minimal
pattern: dots
curvature: soft
animation_preference: static
```

**Rationale**:
- **minimal**: Core philosophy of the brand
- **dots**: Strategic placement, not decorative clutter
- **soft**: Approachable minimalism (not austere)
- **static**: Premium, timeless feel

```

**SVG Result**:
- Hero backgrounds: 4 strategic dots in corners
- Features: Minimal separated elements with spacing
- Stats: 4 circle accents, high contrast with background
- Maximum whitespace; only essential elements

---

### Example 4: Financial/Corporate

```markdown
## 10. Visual Style Preference

Structured, professional, emphasizing order and precision.

```yaml
visual_style_preference: geometric
pattern: mesh
curvature: sharp
animation_preference: static
```

**Rationale**:
- **geometric**: Structured, mathematical, trustworthy
- **mesh**: Lattice/triangular mesh suggests complexity, data
- **sharp**: Professional, precise, no ambiguity
- **static**: Serious, stable, corporate feel

```

**SVG Result**:
- Hero backgrounds: Geometric shapes, symmetrical layouts
- Features: Structured rectangles in grid, mesh overlays
- Stats: Polygonal shapes, precise positioning
- All 90° angles, mathematical precision

---

## Writing the Section Heading & Description

The section heading should be descriptive of your theme's visual philosophy:

```markdown
## 10. Visual Style Preference

[2-3 paragraph description of the visual strategy]

```yaml
visual_style_preference: tech
pattern: grid
curvature: sharp
animation_preference: static
```
```

**Good descriptions** explain:
- **Why** this visual style matches your brand
- **Who** it appeals to (target audience)
- **What** feeling/energy it conveys
- **How** it supports your content (data-driven? human-centered? premium?)

**Example (good)**:
```
A clean, data-driven aesthetic reflecting our commitment to clarity and precision.
Straight lines and grids reinforce the technical nature of our product while
remaining accessible to users. Sharp curves give the design edge without sacrificing
friendliness.
```

**Example (poor)**:
```
We like modern design.
```

---

## Validation

### Check Your Section 10

```bash
# Validate theme's DESIGN.md section 10
aio theme validate linear

# If section 10 is incomplete or missing, you'll see:
# "DESIGN.md section 10 (Visual Style Preference) not found or incomplete;
#  using defaults (tech/geometric/sharp/static)"
```

### Test Your Section 10

```bash
# After editing DESIGN.md, rebuild to see SVG compositions
# updated to your new section 10 settings

aio build slides.md --theme my-theme

# In HTML output, check <svg> elements for:
# - Grid patterns (tech) vs. waves (organic)
# - Sparse dots (minimal) vs. regular meshes (geometric)
# - Sharp angles vs. soft/rounded edges
```

---

## Common Pitfalls

| Mistake | Problem | Fix |
|---------|---------|-----|
| **Missing entire section 10** | Falls back to defaults (tech) | Add section 10 heading and YAML block |
| **Typo in field name** | Field ignored, default used | Check exact spelling (visual_style_preference, not visual_preference) |
| **Invalid value** (e.g., `pattern: squares`) | Field ignored, default used | Use only allowed values from table above |
| **Only partial YAML** (e.g., missing `curvature`) | Partial defaults applied | Ensure all 4 fields present |
| **YAML formatting error** | Entire block fails to parse | Use online YAML validator; check indentation |

---

## Integration with Composition Types

All 8 SVG composition types **respond to section 10**:

| Type | Tech | Organic | Minimal | Geometric |
|------|------|---------|---------|-----------|
| hero-background | Grid overlay, circles | Waves, ellipses | 4 dots, high contrast | Perfect circles, symmetry |
| feature-illustration | Columns + grid | Flowing shapes | Minimal separation | Structured layout |
| stat-decoration | Grid cells | Curved accents | Strategic dots | Polygon grid |
| section-divider | Horizontal stripes | Flowing wave | Thin line accent | Geometric pattern |
| abstract-art | Grid pattern | Organic curves | Sparse elements | Structured mesh |
| process-steps | Numbered grid | Flowing flow arrows | Minimal numbered circles | Regular polygon steps |
| comparison-split | Side-by-side grid | Curved divider | High-contrast split | Structured columns |
| grid-showcase | Cells/grid | Rounded cells | Minimal cells | Regular polygon grid |

---

## Next Steps

1. **Audit your existing DESIGN.md**: Does it have section 10? If not, add it
2. **Choose your visual style**: tech, organic, minimal, or geometric
3. **Select pattern, curvature, animation**: Use decision matrices above
4. **Write your description**: 2-3 sentences explaining the choice
5. **Validate**: `aio theme validate my-theme`
6. **Test**: Build a deck with your theme; check SVG compositions in HTML
7. **Iterate**: Adjust section 10 until compositions match your vision

---

## Questions?

- Check `specs/004-svg-composites-api/contracts/svg-composites.md` for technical details
- Review built-in themes for examples: `src/aio/themes/{linear,vibrant,minimal}/DESIGN.md`
- Report issues: https://github.com/renatobardi/aio/issues
