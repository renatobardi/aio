# Feature Specification: AIO Phase 2 — Visual Enrichment

**Feature Branch**: `feat/003-visual-enrichment`  
**Created**: 2026-04-12  
**Status**: Draft  
**Input**: User description: "AIO Fase 2: Visual Enrichment — SVG icon library (~200 Lucide icons), DataViz engine (bar charts, donuts, sparklines, timelines em SVG puro), markdown syntax para ícones/dados, CSS decorações por tema, e image enrichment via Pollinations.ai (--enrich flag)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — SVG Icon Library (Priority: P1)

A slide designer uses `<!-- @icon: brain -->` in their Markdown file to insert a named SVG icon inline, without depending on any CDN, Figma export, or emoji workaround. The icon is resolved from a bundled library of 200+ Lucide icons and embedded directly in the output HTML.

**Why this priority**: Inline icons are the most frequent visual enrichment request. They are entirely offline-compatible and have no runtime dependencies, making them safe and immediately deliverable. All other Phase 2 features build on the metadata parsing introduced here.

**Independent Test**: Create a single-slide deck containing `<!-- @icon: brain -->`. Build it with `aio build`. Verify the output HTML contains a self-contained `<svg class="icon icon-brain">` element with no external URL references.

**Acceptance Scenarios**:

1. **Given** a slide with `<!-- @icon: brain -->`, **When** the build runs, **Then** the output HTML contains an inline SVG with class `icon icon-brain` and no external references.
2. **Given** `<!-- @icon: brain -->`, `<!-- @icon-size: 64px -->`, `<!-- @icon-color: #635BFF -->`, **When** the build runs, **Then** the SVG element is 64×64 and the color value is applied via inline style or CSS.
3. **Given** `<!-- @icon: unknown-icon -->`, **When** the build runs, **Then** a warning is logged, a fallback icon is rendered, and the build completes successfully.
4. **Given** a user runs `aio icons list`, **Then** at least 200 icon names with their tag categories are printed to stdout in under 100 ms.

---

### User Story 2 — Native DataViz Engine (Priority: P2)

A data analyst authoring a slide deck uses `<!-- @chart: bar -->` and `<!-- @data: Q1:50, Q2:75, Q3:90 -->` to generate a bar chart as a static inline SVG — no JavaScript charting library required. The same syntax works for donuts, sparklines, and timelines.

**Why this priority**: DataViz is the second most impactful visual enrichment. It keeps the output fully offline-capable and eliminates JS dependencies for data presentation.

**Independent Test**: Create a slide with `<!-- @chart: bar -->` and `<!-- @data: Q1:50, Q2:75 -->`. Build and verify the output HTML contains a valid inline `<svg>` bar chart with labeled axes and no external URLs.

**Acceptance Scenarios**:

1. **Given** `<!-- @chart: bar -->` and `<!-- @data: Q1:50, Q2:75, Q3:90, Q4:85 -->`, **When** the build runs, **Then** the output contains a self-contained SVG bar chart with four labeled bars and an auto-scaled Y-axis.
2. **Given** `<!-- @chart: donut -->` and `<!-- @data: Python:45, JavaScript:30, Go:15, Rust:10 -->`, **When** rendered, **Then** the SVG contains four distinct segments with a center label and a legend.
3. **Given** `<!-- @chart: sparkline -->` and `<!-- @data: 10, 25, 18, 32 -->`, **When** rendered, **Then** a compact SVG polyline with filled area is inlined within the slide.
4. **Given** `<!-- @chart: timeline -->` and multi-line `@data` with dated milestones, **When** rendered, **Then** a vertical timeline SVG with dots and labels is produced.
5. **Given** `<!-- @data: -->` (empty), **When** the build runs, **Then** a warning is logged and an empty-state chart is rendered; the build does not halt.

---

### User Story 3 — CSS Decorations per Theme (Priority: P3)

A theme developer adds a new "Decorations" section (section 12) to a theme's `DESIGN.md` to define gradients, dividers, glow effects, and accent lines. A slide author then applies these via `<!-- @decoration: gradient -->` so the slide's background inherits the theme's primary gradient without writing raw HTML or CSS.

**Why this priority**: Decorations raise the visual quality of all slides. They are purely additive and do not break existing layouts, making them safe to ship early.

**Independent Test**: Add section 12 to the `minimal` theme's `DESIGN.md` with one gradient definition. Build a slide with `<!-- @decoration: gradient -->`. Verify the `<section>` element has the gradient applied via CSS class or inline style, and that no raw CSS leaks into the Markdown source.

**Acceptance Scenarios**:

1. **Given** a theme `DESIGN.md` with a Decorations section defining a primary gradient, **When** a slide uses `<!-- @decoration: gradient -->`, **Then** the slide's `<section>` element receives the corresponding CSS class or inline style.
2. **Given** a theme without a section 12, **When** the build runs, **Then** default decoration fallbacks are applied and the build succeeds without errors.
3. **Given** `decorations: false` in `config.yaml`, **When** the build runs, **Then** no decoration classes are applied, even if `@decoration` tags are present.

---

### User Story 4 — Image Enrichment via Pollinations.ai (Priority: P4)

A user runs `aio build --enrich` to automatically generate a contextual image for each slide using the Pollinations.ai free API. Images are base64-encoded and inlined in the output HTML, preserving the standalone, offline-capable output contract.

**Why this priority**: Enrichment is optional and depends on an external API, making it the right candidate for later delivery. The `--enrich` flag is an explicit opt-in, and the feature degrades gracefully if the API is unreachable.

**Independent Test**: Run `aio build --enrich` on a 2-slide deck. Verify the output HTML contains `data:image/jpeg;base64,` `<img>` tags, no external image URLs, and that `aio build` (without `--enrich`) on the same deck produces identical output to a Phase 1 build.

**Acceptance Scenarios**:

1. **Given** `aio build --enrich` on a 5-slide deck, **When** the build completes, **Then** the output HTML contains base64-inlined images and zero external image URLs.
2. **Given** a slide with `<!-- @image-prompt: A futuristic AI brain -->`, **When** `--enrich` is active, **Then** the explicit prompt is used rather than an inferred one.
3. **Given** the Pollinations.ai API is unreachable, **When** `--enrich` is active, **Then** a warning is logged per affected slide, a placeholder SVG is used, and the build completes.
4. **Given** `aio build` without `--enrich`, **When** the build runs, **Then** no API call is made and the build is functionally identical to a Phase 1 build.
5. **Given** the same deck built twice with `--enrich`, **When** both outputs are compared, **Then** the generated images are identical (deterministic seed).

---

### User Story 5 — Unified Build Pipeline Integration (Priority: P5)

The build pipeline transparently incorporates all Phase 2 features (icon resolution, DataViz generation, decorations, enrichment) without requiring any change to the Phase 1 command interface. A `--dry-run` flag allows inspection of what would happen at each pipeline step.

**Why this priority**: Pipeline correctness is a precondition for all previous stories, but it is listed last because it is validated by testing the features above. The `--dry-run` flag is a developer convenience.

**Independent Test**: Build a deck combining `@icon`, `@chart`, and `@decoration` tags. Verify the output HTML is self-contained (no external URLs), that build time for 5 slides without `--enrich` remains under 2 s, and that `--dry-run` prints all step names without writing any file.

**Acceptance Scenarios**:

1. **Given** a deck with icon, chart, and decoration metadata, **When** the build runs, **Then** all three are resolved and the output HTML is self-contained.
2. **Given** `aio build --dry-run`, **When** executed, **Then** all pipeline step names are printed to stderr and no output file is created.
3. **Given** both `@layout` and `@chart` on the same slide, **When** the build runs, **Then** a warning is logged stating chart takes precedence and the build completes.

---

### Edge Cases

- Icon name does not exist in registry → fallback question-mark icon rendered; warning logged.
- `@data` value is empty string → empty-state chart rendered; warning logged; build continues.
- Chart label exceeds readable length → label truncated with ellipsis in the chart.
- Donut chart with one segment at ≥ 99% → tiny segment still rendered (not collapsed); label may be placed outside.
- Timeline with 50+ events → events stacked vertically; horizontal scroll applied on mobile.
- `--enrich` with a 1-word slide title → prompt falls back to a generic descriptor ("Abstract presentation slide").
- Pollinations returns an invalid JPEG → binary validation fails; placeholder SVG used; warning logged.
- `@decoration: gradient` combined with a `split-image-text` layout → gradient applied to section background; image overlay preserved.
- Icon name collides with an existing CSS class name (e.g., `content`) → icon class namespaced as `.icon-content` to prevent collision.
- 50+ icons on a single slide → build logs a performance advisory; rendering still completes.

---

## Requirements *(mandatory)*

### Functional Requirements

**P1 — SVG Icon Library**

- **FR-300**: The system MUST include a bundled library of 200+ Lucide icons as self-contained SVG files requiring no external CDN or API.
- **FR-301**: The system MUST parse `<!-- @icon: name -->` metadata tags in slide Markdown and replace them with inline SVG in the rendered HTML.
- **FR-302**: The system MUST support `@icon-size` and `@icon-color` metadata to customise icon dimensions and fill color per slide.
- **FR-303**: The system MUST render a fallback icon and log a warning when an unrecognised icon name is requested, without halting the build.
- **FR-304**: The system MUST provide an `aio icons list [--filter tag]` command that lists available icons with their tag categories.
- **FR-305**: Icon SVG output MUST carry CSS classes `.icon` and `.icon-{name}` to enable theme-level CSS targeting.

**P2 — DataViz Engine**

- **FR-320**: The system MUST generate bar charts, donut charts, sparklines, and timeline charts as inline SVG from `<!-- @chart: type -->` and `<!-- @data: ... -->` metadata.
- **FR-321**: Each generated chart MUST be fully self-contained SVG (no external resources) and must not exceed 5 KB.
- **FR-322**: The DataViz engine MUST auto-scale chart axes based on the provided data values (10% headroom above maximum).
- **FR-323**: Chart colors MUST reference theme CSS custom properties (`--color-primary`, `--color-accent`, etc.) with hard-coded fallbacks when properties are undefined.
- **FR-324**: The system MUST render an empty-state chart and log a warning when `@data` is empty or malformed, without halting the build.
- **FR-325**: Chart output MUST be deterministic: identical input data MUST always produce byte-identical SVG.

**P3 — Markdown Metadata Syntax**

- **FR-340**: The system MUST parse `<!-- @key: value -->` HTML comment syntax as slide metadata; parsed tags MUST NOT appear in the output HTML.
- **FR-341**: Metadata parsing MUST be case-insensitive for keys (`@ICON` and `@icon` are equivalent).
- **FR-342**: Malformed metadata comments MUST be logged as warnings and ignored; they MUST NOT halt the build.
- **FR-343**: When both `@layout` and `@chart` are present on the same slide, the system MUST log a warning and use the chart, ignoring the layout directive.

**P4 — CSS Decorations per Theme**

- **FR-350**: Theme `DESIGN.md` files MAY include a section 12 "Decorations" defining gradients, dividers, glow effects, and accent lines.
- **FR-351**: The system MUST generate CSS classes in `.decoration-{type}-{variant}` format from section 12 definitions.
- **FR-352**: The system MUST apply sensible default decoration styles when a theme omits section 12.
- **FR-353**: Decorations MUST be disabled globally when `decorations: false` is set in `config.yaml`.
- **FR-354**: Decoration CSS MUST be additive and MUST NOT break existing slide layouts.

**P5 — Image Enrichment**

- **FR-360**: The `aio build --enrich` flag MUST trigger image generation for applicable slides using the Pollinations.ai free-tier API.
- **FR-361**: The system MUST use an explicit `<!-- @image-prompt: ... -->` tag when present, falling back to a prompt inferred from the slide title and content (max 100 characters).
- **FR-362**: Generated images MUST be base64-encoded and inlined in the output HTML; the final output MUST contain zero external image URLs.
- **FR-363**: Image generation MUST use a deterministic seed derived from the slide index and deck title, making repeated runs with identical input produce identical images.
- **FR-364**: The system MUST time out per-image API calls after 30 seconds and fall back to a placeholder SVG, logging a warning, without halting the build.
- **FR-365**: The `--enrich` code path MUST be lazily loaded; running `aio build` without `--enrich` MUST produce output identical to a Phase 1 build.

**P6 — Build Pipeline Integration**

- **FR-380**: The build pipeline MUST be extended to resolve icons, generate DataViz SVGs, and apply decorations during the Compose step, with an optional Enrich step between Render and Inline.
- **FR-381**: A `--dry-run` flag MUST print all pipeline step names to stderr and MUST NOT write any output file.
- **FR-382**: Each pipeline step MUST emit a single-line progress indicator to stderr (✓ on success, ✗ on failure).

### Key Entities

- **IconRecord**: Named Lucide icon — id, display name, tag list, SVG path data, viewBox.
- **ChartSpec**: Parsed chart directive — type (bar/donut/sparkline/timeline), data series, optional metadata (title, axis labels, color overrides, dimensions).
- **DecorationSpec**: Parsed decoration directive — decoration type, variant, resolved CSS value.
- **EnrichContext**: Per-slide enrichment state — explicit or inferred prompt, deterministic seed, generated image bytes or placeholder flag.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-300**: A 5-slide deck containing icons, charts, and decorations builds in under 2 seconds without `--enrich`.
- **SC-301**: A 5-slide deck with `--enrich` active completes in under 30 seconds (including API latency).
- **SC-302**: All output HTML files from Phase 2 builds remain fully self-contained: zero external URLs in `href` or `src` attributes.
- **SC-303**: Icon resolution for any of the 200 bundled icons completes in under 1 ms per icon.
- **SC-304**: DataViz chart generation for any supported chart type completes in under 10 ms per chart.
- **SC-305**: `aio icons list` returns results in under 100 ms regardless of filter.
- **SC-306**: An unrecognised icon or malformed `@data` directive never halts the build; a human-readable warning including the slide number is emitted.
- **SC-307**: Two consecutive `aio build --enrich` runs on the same input produce byte-identical output HTML.
- **SC-308**: Builds without `--enrich` are functionally identical to Phase 1 builds — no regressions in existing functionality.
- **SC-309**: `--dry-run` completes in under 100 ms and creates no output files.

---

## Assumptions

- Pollinations.ai free tier does not require an API key; an optional key may be provided for higher quotas but is not mandatory.
- SVG output targets modern ES6-capable browsers; Internet Explorer compatibility is out of scope.
- DataViz charts are static (no hover or zoom interactivity); all visual information must be conveyed by the static rendering alone.
- All Lucide icons share a consistent SVG format with a `viewBox`, `fill="currentColor"`, and a single `<path>` element, allowing uniform path-data extraction.
- Theme CSS custom properties (`--color-primary`, etc.) are always defined in the theme stylesheet; the DataViz engine uses sensible hard-coded fallbacks if they are absent.
- The Phase 1 pipeline is stable; Phase 2 extends it without modifying existing public interfaces.
- Image enrichment is an optional enhancement; slides without `--enrich` render identically to Phase 1 output.
- Markdown slide content is always present when `@image-prompt` is absent; the prompt inference always has something to work with.
- The `--enrich` flag is intended for authoring time, not continuous integration; 30 s per image is an acceptable latency in that context.
- Decorations are additive CSS classes; they do not require changes to existing Jinja2 layout templates unless a template explicitly opts in.
