# Quickstart: AIO Phase 2 — Visual Enrichment (M2.5)

**Phase 1 Output** | **Date**: 2026-04-12

This guide extends `specs/002-core-layouts-theme-system/quickstart.md`. Only Phase 2 additions are documented here.

---

## Dev Setup (incremental from M1)

```bash
# No new deps required for core Phase 2 features
pip install -e ".[dev]"

# Image enrichment support (Pollinations.ai client + image validation)
pip install -e ".[enrich]"    # adds pillow for JPEG validation

# Run Phase 2 tests
pytest tests/unit/test_inline_metadata.py -v
pytest tests/unit/test_icons.py -v
pytest tests/unit/test_dataviz_phase2.py -v
pytest tests/unit/test_decorations.py -v
pytest tests/unit/test_enrich.py -v
pytest tests/integration/test_build_phase2.py -v
```

---

## Feature Workflow Recipes

### Recipe 1 — Add an icon to a slide

```markdown
---
layout: hero-title
---

<!-- @icon: sparkles -->
<!-- @icon-size: 96px -->
<!-- @icon-color: #FFD700 -->

# Visual Enrichment

Modern, offline-first presentations.
```

Build and verify:
```bash
aio build slides.md -o out.html
grep 'icon-sparkles' out.html       # should match
grep 'http' out.html                # should NOT match (Art. II check)
```

### Recipe 2 — Add a bar chart

```markdown
---

<!-- @chart: bar -->
<!-- @data: Q1:50, Q2:75, Q3:90, Q4:85 -->
<!-- @title: Revenue by Quarter -->
<!-- @y-axis: Revenue ($K) -->

### Financial Performance
```

Verify the SVG was inlined:
```bash
aio build slides.md -o out.html
python -c "
import re, sys
html = open('out.html').read()
bad = re.findall(r'(?:href|src)=[\"\'](https?://[^\"\']+)[\"\'']', html)
print('FAIL:', bad) if bad else print('PASS')
"
```

### Recipe 3 — Build with image enrichment

```bash
aio build slides.md -o out.html --enrich
```

Expected stderr output:
```
[INFO] Step 4.5/6: ENRICH
[DEBUG] Slide 1: enriched ✓
[DEBUG] Slide 3: enriched ✓
```

Verify images are base64-inlined (no external URLs):
```bash
grep 'data:image/jpeg;base64,' out.html | wc -l   # should equal enriched slide count
grep 'pollinations\|https://' out.html             # should be 0
```

### Recipe 4 — Discover available icons

```bash
aio icons list                     # all 200+ icons
aio icons list --filter dataviz    # filter by tag
aio icons list --count             # just the number
```

### Recipe 5 — Dry run to inspect pipeline

```bash
aio build slides.md -o out.html --dry-run
```

Expected output (no file written):
```
[INFO] --dry-run: pipeline steps would be:
[INFO]   Step 1/5: PARSE
[INFO]   Step 2/5: ANALYZE
[INFO]   Step 3/5: COMPOSE
[INFO]   Step 4/5: RENDER
[INFO]   Step 5/5: INLINE
[INFO] --dry-run: no output written.
```

### Recipe 6 — Apply a decoration

```markdown
---

<!-- @decoration: gradient -->

# Bold Statement

Supporting copy goes here.
```

The rendered `<section>` will carry `class="slide decoration-gradient-primary"`.

---

## Testing Conventions (Phase 2 additions)

### Unit tests — `tests/unit/`

| File | What it tests |
|------|--------------|
| `test_inline_metadata.py` | `<!-- @key: value -->` extraction, precedence rules, edge cases |
| `test_icons.py` | `render_icon()`, fallback behaviour, `list_icons()` |
| `test_dataviz_phase2.py` | `DonutChart`, `SparklineChart`, `TimelineChart` — SVG output, edge cases |
| `test_decorations.py` | `DecorationSpec` parsing, CSS generation, fallback defaults |
| `test_enrich.py` | `EnrichContext`, prompt inference, seed derivation, JPEG validation, placeholder fallback |

### Integration tests — `tests/integration/`

| File | What it tests |
|------|--------------|
| `test_build_phase2.py` | Full pipeline with icon + chart + decoration combinations; no mocks for pipeline steps |
| `test_build_enrich.py` | `--enrich` flag with mocked Pollinations responses; validates base64 embedding and Art. II compliance |

### Fixtures — `tests/fixtures/`

| File | Used by |
|------|---------|
| `slides_phase2.md` | Integration tests — deck with all Phase 2 directives |
| `mock_pollinations_response.jpg` | `test_build_enrich.py` — pre-baked JPEG bytes |
| `expected_bar_chart.svg` | `test_dataviz_phase2.py` — determinism check |

---

## TDD Cycle for Phase 2

1. Write test in `tests/unit/test_{module}.py` — confirm it fails (`pytest -k test_name` exits 1).
2. Implement the feature in `src/aio/...`.
3. Run the test again — confirm it passes.
4. Run the full suite: `pytest tests/ -v --cov=src/aio --cov-report=term-missing`.
5. Confirm coverage did not regress below the current baseline.

---

## Key File Locations

| File | Purpose |
|------|---------|
| `src/aio/visuals/svg/icons.py` | Extended Lucide icon library (200+) with `render_icon()` and `list_icons()` |
| `src/aio/visuals/dataviz/charts.py` | Extended chart engine: adds DonutChart, SparklineChart, TimelineChart |
| `src/aio/commands/icons.py` | `aio icons list` CLI subcommand |
| `src/aio/_enrich.py` | EnrichEngine + Pollinations.ai client (lazy-loaded) |
| `src/aio/themes/parser.py` | Extended to parse DESIGN.md section 12 → `DecorationSpec[]` |
| `src/aio/composition/metadata.py` | Extended SlideRenderContext (icon_name, chart_svg, decoration_class, image_prompt) |
| `src/aio/commands/build.py` | --enrich and --dry-run flags; Enrich step wired in |
