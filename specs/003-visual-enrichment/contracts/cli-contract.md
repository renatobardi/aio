# CLI Contract: AIO Phase 2 — Visual Enrichment

**Phase 1 Output** | **Date**: 2026-04-12

This document extends the M1 CLI contract (`specs/002-core-layouts-theme-system/contracts/cli-contract.md`) with Phase 2 additions only. Existing commands are unchanged unless explicitly noted below.

---

## Modified Commands

### `aio build`

**New options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--enrich` | flag | `False` | Enable image enrichment via Pollinations.ai (Step 4.5) |
| `--dry-run` | flag | `False` | Print pipeline steps to stderr; write no output file |

**Exit codes (unchanged from M1, plus):**

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (parse, render, etc.) |
| 3 | External URL detected in output HTML (Art. II violation) |

**Stderr (with `--dry-run`):**
```
[INFO] --dry-run: pipeline steps would be:
[INFO]   Step 1/5: PARSE
[INFO]   Step 2/5: ANALYZE
[INFO]   Step 3/5: COMPOSE
[INFO]   Step 4/5: RENDER
[INFO]   Step 5/5: INLINE
[INFO] --dry-run: no output written.
```

**Stderr (with `--enrich`, 5-slide deck, `--verbose`):**
```
[INFO] Step 1/6: PARSE
[DEBUG] Parsed 5 slides
[INFO] Step 2/6: ANALYZE
[INFO] Step 3/6: COMPOSE
[DEBUG] Slide 1: icon=sparkles ✓
[DEBUG] Slide 2: chart=bar ✓
[INFO] Step 4/6: RENDER
[INFO] Step 4.5/6: ENRICH
[DEBUG] Slide 2: enriched (seed=1234567890) ✓
[DEBUG] Slide 4: enrich failed — using placeholder ✗
[INFO] Step 5/6: INLINE
[INFO] Build complete: out.html (2.8 MB)
```

---

## New Commands

### `aio icons`

Top-level subcommand group for icon discovery.

```
aio icons [COMMAND]
```

#### `aio icons list`

List all available icons in the bundled Lucide library.

**Usage:**
```
aio icons list [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--filter TEXT` | str | `""` | Filter by tag substring (case-insensitive) |
| `--count` | flag | `False` | Print only the total count, not the icon list |

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid filter expression |

**Stdout (default — table format):**
```
brain          Tags: ai, mind, intelligence
chart-bar      Tags: dataviz, analytics, bar
code           Tags: development, programming
...
(200 icons)
```

**Stdout (`--count`):**
```
200
```

**Stdout (`--filter dataviz`):**
```
bar-chart      Tags: dataviz, analytics
chart-bar      Tags: dataviz, analytics, bar
chart-line     Tags: dataviz, analytics, line
...
(N icons matching filter)
```

**Performance:** Must complete in < 100 ms for 200+ icons, no filter.

---

## Inline Metadata Syntax (Markdown DSL)

Not a CLI command, but documented here as the user-facing contract for slide authors.

### Syntax

```
<!-- @key: value -->
```

All directives are HTML comments placed in the body of a slide (between `---` separators). They are removed from the output HTML.

### Supported Directives

| Directive | Value Format | Example | Notes |
|-----------|-------------|---------|-------|
| `@icon` | icon name (slug) | `<!-- @icon: brain -->` | Icon from bundled Lucide library |
| `@icon-size` | CSS length | `<!-- @icon-size: 64px -->` | Defaults to 48px |
| `@icon-color` | CSS color or hex | `<!-- @icon-color: #635BFF -->` | Defaults to `var(--color-primary)` |
| `@chart` | chart type | `<!-- @chart: bar -->` | bar, donut, sparkline, line, pie, timeline |
| `@data` | key:value pairs or csv | `<!-- @data: Q1:50, Q2:75 -->` | Multi-line for timeline |
| `@title` | string | `<!-- @title: Revenue by Quarter -->` | Chart/slide title |
| `@y-axis` | string | `<!-- @y-axis: Growth (%) -->` | Bar/line Y-axis label |
| `@height` | CSS length | `<!-- @height: 40px -->` | Sparkline height override |
| `@color` | CSS color or hex | `<!-- @color: #635BFF -->` | Sparkline/timeline color override |
| `@decoration` | decoration type | `<!-- @decoration: gradient -->` | gradient, border, shadow, glow |
| `@decoration-type` | variant name | `<!-- @decoration-type: primary -->` | Selects sub-variant |
| `@image-prompt` | free text | `<!-- @image-prompt: A futuristic AI... -->` | Explicit enrichment prompt |

### Precedence rules

1. YAML frontmatter keys take precedence over HTML comment keys when both define the same field.
2. When both `@layout` (HTML comment or frontmatter) and `@chart` are present, `@chart` takes precedence and a warning is emitted.
3. Multiple `@icon` directives on the same slide → only the last one is used; a warning is emitted.

### Error handling

| Error Type | Behaviour |
|------------|-----------|
| Unknown icon name | Warning logged; fallback `help-circle` icon rendered |
| Unknown chart type | Warning logged; slide rendered without a chart |
| Malformed `@data` | Warning logged; empty-state chart rendered |
| Empty `@data` | Warning logged; empty-state chart rendered |
| `@icon-size` invalid CSS | Warning logged; defaults to `48px` |
| `@icon-color` invalid CSS | Warning logged; defaults to `var(--color-primary)` |
| Unrecognised directive key | Warning logged; directive ignored |
