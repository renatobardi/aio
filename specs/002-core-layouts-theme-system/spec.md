# Feature Specification: AIO Core Layouts & Theme System (M1)

**Feature Branch**: `002-core-layouts-theme-system`
**Created**: 2026-04-11
**Status**: Draft
**Input**: AIO Fase 1 — 6 user stories (P1–P6) covering 8 production-ready layouts, 64+ themes from awesome-design-md, DESIGN.md 11-section schema, advanced Theme CLI, build pipeline v2, and serve with hot reload.

---

## Clarifications

### Session 2026-04-11

- Q: Should the hot-reload notification channel use SSE or WebSocket? → A: SSE (Server-Sent Events) — unidirectional, simpler, no upgrade handshake needed for a one-way reload signal.
- Q: How does the import script access awesome-design-md? → A: `git clone https://github.com/nicholasgasior/awesome-design-md` for initial import; `git pull` for incremental nightly syncs; parse the local checkout.
- Q: What is the default bind address for `aio serve`? → A: `127.0.0.1` (localhost only); users who need LAN access pass `--host 0.0.0.0` explicitly.

---

## Context & Problem Statement

M0 delivered a working CLI skeleton and project scaffolding, but without concrete layouts and themes the generator produces no usable output. Developers and designers need:

1. **8+ production-ready layouts** (hero, stat, split-image-text, comparison, quote, key-takeaways, closing, etc.) that work immediately after `aio init`
2. **64+ professional themes** imported from awesome-design-md with an automatic import script and nightly sync
3. **DESIGN.md structured format** with 11 mandatory sections (visual, colors, typography, components, layout, depth, do/don't, responsive, accessibility, visual composition, layout components)
4. **Advanced Theme CLI** (list with filters, search, info, use, show, create)
5. **Build pipeline v2** with Parse → Analyze → Compose → Render → Inline steps and automatic layout inference
6. **Serve with hot reload** — theme changes reflected instantly via SSE (Server-Sent Events at `/__sse__`)

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — 8 Core Layouts Production-Ready (Priority: P1)

A new AIO user runs `aio build` and gets 8 visually coherent layout types rendered without writing any Jinja2 or CSS.

**Why this priority**: Without layouts, no build is possible. Everything else in M1 depends on a working render pipeline.

**Independent Test**: Given a `slides.md` file using each of the 8 `@layout:` directives, run `aio build slides.md -o out.html` and verify the output HTML contains the expected `<section class="layout-{name}">` structure for each layout.

**Acceptance Scenarios**:

1. **Given** a slide with `<!-- @layout: hero-title -->`, `<!-- @title: Welcome -->`, `<!-- @subtitle: Your AI-native presentation -->`, **When** build executes, **Then** the output HTML contains `<section class="layout-hero-title">`, `<h1 class="hero-title">Welcome</h1>`, `<p class="hero-subtitle">Your AI-native presentation</p>`; font-size and color come from theme CSS variables; a media query scales the heading on mobile.

2. **Given** a slide with `<!-- @layout: stat-highlight -->`, `<!-- @stat: 87% -->`, `<!-- @label: Accuracy -->`, `<!-- @description: Across all 50K test cases -->`, **When** build executes, **Then** HTML contains `<span class="stat">87%</span>`, `<p class="stat-label">Accuracy</p>`, `<p class="stat-description">Across all 50K test cases</p>`; stat is centered with a giant font (≥ 64px).

3. **Given** a slide with `<!-- @layout: split-image-text -->`, `<!-- @image: /assets/diagram.png -->`, `<!-- @title: How AIO Works -->`, plus body text, **When** build executes, **Then** the left half is `<img>` (base64-inlined, alt attribute set) and the right half is a `<div class="content">` containing the title and rendered markdown; CSS grid is 50%/50%.

4. **Given** a slide with `<!-- @layout: comparison-2col -->` with `@left-title`, `@left-content`, `@right-title`, `@right-content` tags, **When** build executes, **Then** two columns render with distinct heading classes and the content renders as markdown lists.

5. **Given** a slide with `<!-- @layout: quote -->`, `<!-- @quote: Innovation is about saying no. -->`, `<!-- @author: Steve Jobs -->`, **When** build executes, **Then** output contains `<blockquote class="layout-quote">` and `<p class="quote-author">— Steve Jobs</p>` with large italic styling and a left border accent.

6. **Given** a `slides.md` with any of the 8 layouts but no theme override, **When** `aio build` runs, **Then** each layout renders with sensible defaults (legible font, colors from `--color-primary` etc.); no external CSS is referenced.

7. **Given** a slide with `<!-- @layout: key-takeaways -->` and a list of bullet points in body text, **When** build executes, **Then** each bullet renders with a checkmark glyph (`✓`) and appropriate spacing.

8. **Given** a slide with `<!-- @layout: closing -->`, `<!-- @title: Thank You -->`, `<!-- @cta: Start with aio init -->`, **When** build executes, **Then** the CTA renders as a prominent call-to-action block.

---

### User Story 2 — Theme System: 64+ Themes from awesome-design-md (Priority: P1)

A designer picks `--theme stripe` at init or switches later with `aio theme use stripe` and the build renders all 8 layouts with Stripe's colors, fonts, and component styles.

**Why this priority**: Themes are the visual layer above layouts. Both P1 stories must ship together.

**Independent Test**: Run `aio theme list` and verify ≥ 64 entries; run `aio init test-stripe --theme stripe` and verify `.aio/config.yaml` contains `theme: stripe` and `.aio/themes/registry.json` has the Stripe metadata; run `aio build slides.md -o out.html` and verify the output CSS contains `--color-primary: #635BFF`.

**Acceptance Scenarios**:

1. **Given** `scripts/import-awesome-designs.py` is executed, **When** it completes, **Then**: ≥ 64 theme directories exist under `src/aio/themes/{id}/`; each has `DESIGN.md`, `theme.css`, `layout.css`, `meta.json`; `src/aio/themes/registry.json` has ≥ 64 entries; the script exits 0 and logs `✓ Imported N themes`.

2. **Given** `aio init proj --theme stripe`, **When** init runs, **Then** `.aio/config.yaml` contains `theme: stripe`; `.aio/themes/registry.json` contains only the Stripe theme entry (not the full 64); init exits 0 in under 1 second.

3. **Given** `aio theme list`, **When** executed, **Then** stdout shows a rich table with columns ID, Name, Author, Categories; ≥ 64 rows; runs in under 1 second.

4. **Given** `aio theme list --filter design-system`, **When** executed, **Then** only themes tagged `design-system` are shown; count is ≥ 20.

5. **Given** a project using theme `stripe`, **When** `aio build` produces `out.html`, **Then** the inlined CSS contains the Stripe design variables (`--color-primary: #635BFF`, `--font-display: Inter`, etc.); no external stylesheet is referenced.

6. **Given** the global registry has 64+ themes but a project uses only `stripe`, **When** `aio init` or `aio theme use` runs, **Then** only the selected theme's metadata is written to `.aio/themes/registry.json` (not all 64).

---

### User Story 3 — DESIGN.md Format: 11-Section Specification (Priority: P2)

A theme developer writes or edits a `DESIGN.md` and `aio theme validate` confirms it parses correctly into CSS variables and layout overrides.

**Why this priority**: Without a machine-parseable DESIGN.md, extract.py and the agent prompt snippet cannot work. Required before M2.

**Independent Test**: Given a valid `DESIGN.md` for the `stripe` theme, run `aio theme validate stripe` and verify exit code 0; run `aio extract` (or the extract helper) and verify `theme.css` contains `--color-primary: #635BFF` matching the DESIGN.md Color Palette section.

**Acceptance Scenarios**:

1. **Given** a `DESIGN.md` with all 11 sections (Visual Theme, Color Palette, Typography, Components, Layout System, Depth & Shadows, Do's & Don'ts, Responsive Behavior, Animation & Transitions, Accessibility, Agent Prompt Snippet), **When** `aio theme validate {id}` runs, **Then** exit code is 0 and stdout says `✓ Theme '{id}' is valid`.

2. **Given** the Color Palette section contains `- Primary: #635BFF` and `- Accent: #00D084`, **When** `extract.py` processes the file, **Then** `theme.css` contains `:root { --color-primary: #635BFF; --color-accent: #00D084; }`.

3. **Given** the Typography section specifies `Display Font: Inter`, **When** `extract.py` processes the file, **Then** `theme.css` contains `--font-display: 'Inter'` and optionally a Google Fonts import directive (inlined, not an external link).

4. **Given** a `DESIGN.md` is missing section 9 (Animation & Transitions), **When** `extract.py` processes it, **Then** a warning is logged and parsing continues with defaults; exit code remains 0; no crash.

5. **Given** a `DESIGN.md` with invalid YAML or malformed hex color (`#ZZZZZZ`), **When** `aio theme validate {id}` runs, **Then** exit code is 1; stderr lists the specific validation errors.

---

### User Story 4 — Theme CLI: list, search, info, use, show, create (Priority: P2)

A developer can manage all theme lifecycle operations from the terminal without editing files manually.

**Why this priority**: Needed alongside themes being available. Enables discovery and project customization.

**Independent Test**: Run `aio theme list`, `aio theme info stripe`, `aio theme use stripe`, `aio theme show stripe`, `aio theme create custom-theme --from stripe` sequentially in a project directory and verify each exits 0 with appropriate output.

**Acceptance Scenarios**:

1. **Given** `aio theme list --limit 10`, **When** executed, **Then** a rich table shows at most 10 rows with columns ID, Name, Author, Categories; runs in under 1 second.

2. **Given** `aio theme list --filter design-system,fintech`, **When** executed, **Then** only themes tagged with both `design-system` AND `fintech` are shown (intersection).

3. **Given** `aio theme info stripe`, **When** executed, **Then** output shows Name, Author, Categories, Source URL, Colors (primary/accent/neutral hex), Typography (display/body fonts); exits 0.

4. **Given** `aio theme info stripe --json`, **When** executed, **Then** stdout is valid JSON with keys `id`, `name`, `author`, `categories`, `colors`, `typography`; can be piped to `jq`.

5. **Given** `aio theme use stripe` inside a project with `.aio/config.yaml`, **When** executed, **Then** `config.yaml` is updated to `theme: stripe`; `.aio/themes/registry.json` is updated with Stripe metadata; stdout says `✓ Switched theme to 'stripe'. Run 'aio serve' to preview.`; completes in under 100ms.

6. **Given** `aio theme show stripe`, **When** executed, **Then** the full DESIGN.md of the stripe theme is printed to stdout.

7. **Given** `aio theme show stripe --section 2`, **When** executed, **Then** only the Color Palette section is printed.

8. **Given** `aio theme create my-theme --from stripe`, **When** executed, **Then** `src/aio/themes/my-theme/` is created with copies of `DESIGN.md`, `theme.css`, `layout.css`, `meta.json`; the new theme is added to the global registry; stdout says `✓ Created custom theme 'my-theme' based on 'stripe'`.

9. **Given** `aio theme use unknown-id` in a project, **When** executed, **Then** exit code is 2; stderr says `Theme 'unknown-id' not found in registry`.

10. **Given** `aio theme search "design"`, **When** executed, **Then** at least 40 themes match via fuzzy match; results include Apple, Stripe, Linear, Figma; runs in under 1 second.

---

### User Story 5 — Build Pipeline v2: Parse → Analyze → Compose → Render → Inline (Priority: P2)

The build command executes 5 clearly-logged steps, infers layouts automatically, and produces a single self-contained HTML file; errors point to the exact failing step.

**Why this priority**: The v1 pipeline stub is insufficient for real output. Required before M2 visual features.

**Independent Test**: Given a `slides.md` with 5 slides using various layouts, run `aio build slides.md -o out.html` and verify: exit code 0; `out.html` exists; the file contains `reveal.js` initializer; no external URLs (`https://`) appear in the output; all 5 slides have a `<section>` tag.

**Acceptance Scenarios**:

1. **Given** a valid `slides.md` with 5 slides, **When** `aio build` runs, **Then** the 5 pipeline steps are logged at INFO level (`Step 1/5: PARSE`, etc.); `out.html` is a single file with all CSS, JS, and Reveal.js inlined; external-URL check passes; exit code 0.

2. **Given** a slide with `<!-- @layout: auto -->` and a body containing a percentage statistic, **When** the Analyze step runs, **Then** the layout is inferred as `stat-highlight` and the relevant context metadata is extracted.

3. **Given** the selected theme is `stripe`, **When** the Render step runs, **Then** Stripe's `theme.css` and `layout.css` are read from disk and inlined into the output HTML.

4. **Given** a slide references an unknown layout `<!-- @layout: galaxy-brain -->`, **When** `aio build` runs, **Then** a WARNING is logged naming the unknown layout; the slide falls back to the `content` layout; build continues and exits 0.

5. **Given** `--dry-run` is passed, **When** `aio build` runs, **Then** all 5 steps are executed and logged, but no output file is written; final log shows `[dry-run] Would write {N} bytes to out.html`.

6. **Given** `slides.md` contains a `<!-- @layout: split-image-text -->` with `@image: /assets/photo.jpg` (file exists), **When** the Inline step runs, **Then** the image is read, converted to base64, and embedded as a `data:image/jpeg;base64,...` URI; no file path reference remains in the HTML.

7. **Given** the build encounters a missing theme CSS file, **When** it fails, **Then** exit code is 2 (theme not found or invalid); stderr clearly names the missing file and the failing step.

---

### User Story 6 — Serve with Hot Reload (Priority: P3)

A developer runs `aio serve slides.md`, edits the file or switches themes, and sees the presentation update in the browser within 2 seconds without restarting the server.

**Why this priority**: Hot reload is a developer experience multiplier that unblocks rapid theme and layout iteration.

**Independent Test**: Run `aio serve slides.md --port 9999`, verify the HTTP server responds at `http://localhost:9999` with 200 and an HTML body; modify `slides.md` and verify the browser receives a reload event within 2 seconds.

**Acceptance Scenarios**:

1. **Given** `aio serve slides.md --port 8080`, **When** executed, **Then** the server starts; `GET http://localhost:8080` returns 200 with HTML body containing the presentation; `GET http://localhost:8080/__sse__` returns `text/event-stream` with an initial `{"type":"connected"}` event.

2. **Given** the server is running and `slides.md` is saved, **When** the file changes, **Then** the server detects the change via watchdog in under 500ms and sends a reload signal; the connected browser refreshes within 2 seconds.

3. **Given** `aio serve` is running and the user runs `aio theme use stripe` in a second terminal, **Then** the config change is detected and the browser reloads with the Stripe theme applied.

4. **Given** port 8080 is already in use, **When** `aio serve --port 8080` runs, **Then** the command detects the conflict, logs a clear error naming the port, and exits with code 2 without starting a server.

5. **Given** `aio serve` is running and the user presses Ctrl+C, **When** SIGINT is received, **Then** the server shuts down gracefully (no zombie processes, clean port release); exit code 0.

---

## Functional Requirements

### P1 — 8 Core Layouts

- **FR-200:** 8 Jinja2 templates in `src/aio/layouts/`: `hero-title.j2`, `stat-highlight.j2`, `split-image-text.j2`, `content-with-icons.j2`, `comparison-2col.j2`, `quote.j2`, `key-takeaways.j2`, `closing.j2`
- **FR-201:** Each layout uses `{% block name %}Default{% endblock %}` syntax; fallbacks are defined
- **FR-202:** All layouts inherit `base.j2` (Reveal.js slide structure)
- **FR-203:** Each layout injects CSS class `.layout-{name}` onto the `<section>` element
- **FR-204:** Images in `split-image-text` are base64-inlined during the Inline step (max 3 MB per image)
- **FR-205:** Layout registry is auto-discovered by scanning `.j2` files in `src/aio/layouts/`
- **FR-206:** Each layout supports 0–10 metadata blocks; missing blocks use per-layout defaults
- **FR-207:** Markdown body content is rendered to HTML via mistune *before* being injected into layout context variables (`title`, `body_html`, etc.); Jinja2 templates receive pre-rendered HTML strings, never raw Markdown
- **FR-208:** Layout CSS is scoped to `.layout-{name}` selectors (no cross-layout leakage)

### P2 — Theme System

- **FR-210:** Global theme registry `src/aio/themes/registry.json` with metadata for ≥ 64 themes
- **FR-211:** Each theme lives in `src/aio/themes/{id}/` with `DESIGN.md`, `theme.css`, `layout.css`, `meta.json`
- **FR-212:** `DESIGN.md` contains all 11 mandatory sections (per FR-220)
- **FR-213:** `theme.css` defines CSS custom properties: `--color-primary`, `--color-accent`, `--color-neutral`, `--font-display`, `--font-body`, etc.
- **FR-214:** `layout.css` defines `.layout-{name}` classes with theme-specific overrides
- **FR-215:** `meta.json` contains: `id`, `name`, `colors` (hex dict), `typography` (fonts dict), `categories` (list), `author`, `source_url`
- **FR-216:** `scripts/import-awesome-designs.py` clones `https://github.com/nicholasgasior/awesome-design-md` on first run (or `git pull` if already cloned), parses the local checkout, creates per-theme directories, generates CSS and meta.json, updates registry.json
- **FR-217:** Nightly GitHub Actions workflow (`.github/workflows/3-sync-themes.yml`) runs the import script and commits changes
- **FR-218:** Project `.aio/themes/registry.json` contains only the selected theme's metadata (not the full global registry)
- **FR-219:** `aio theme use {id}` updates `config.yaml` and `.aio/themes/registry.json` within 100ms

### P3 — DESIGN.md 11-Section Format

- **FR-220:** DESIGN.md defines 11 sections (numbered headings or matching text):
  1. Visual Theme
  2. Color Palette (list: `- Name: #HEX`)
  3. Typography (display/body fonts + size scale)
  4. Components (buttons, cards, badges)
  5. Layout System (grid, spacing, max-widths)
  6. Depth & Shadows (elevation levels)
  7. Do's & Don'ts
  8. Responsive Behavior (breakpoints)
  9. Animation & Transitions (velocities, easing)
  10. Accessibility (WCAG 2.1 AA claims)
  11. Agent Prompt Snippet (~200 words, machine-usable)
- **FR-221:** `extract.py` matches sections by number or heading text (case-insensitive)
- **FR-222:** Color Palette is parsed into `meta.json` `colors` object and `--color-*` CSS vars
- **FR-223:** Typography is parsed into `--font-*` CSS vars
- **FR-224:** Components section generates skeleton `.layout-*` CSS classes
- **FR-225:** Layout System populates `layout.css` with template-specific overrides
- **FR-226:** Missing sections produce WARNING log entries; parsing continues with defaults
- **FR-227:** DESIGN.md remains human-readable markdown throughout

### P4 — Theme CLI

- **FR-230:** `aio theme` subcommand group with 6 subcommands: `list`, `search`, `info`, `use`, `show`, `create`
- **FR-231:** `aio theme list [--limit N] [--filter tag,...] [--search query]` with rich table output
- **FR-232:** `aio theme info {id} [--json]` shows metadata + colors + typography + layout count
- **FR-233:** `aio theme use {id}` validates theme, updates `config.yaml` and `.aio/themes/registry.json`
- **FR-234:** `aio theme show {id} [--section N] [--raw]` outputs the full DESIGN.md (Rich Markdown-rendered) when no `--section` is given, or only section N when specified; `--raw` prints plain text instead of Rich-rendered output (omitting `--section` already shows the full document — no `--all` flag is needed or exposed)
- **FR-235:** `aio theme create {name} [--from template-id]` scaffolds a new theme (copies template if `--from` given)
- **FR-236:** Theme search uses fuzzy matching (Levenshtein distance or `difflib.SequenceMatcher`)
- **FR-237:** `--filter` supports comma-separated tags with AND semantics — a theme must have ALL specified tags to match (e.g., `--filter dark,minimal` returns only themes tagged with both `dark` AND `minimal`)
- **FR-238:** `--json` flag available on `list`, `info`, `search`; output is valid JSON
- **FR-239:** All theme subcommands validate the theme ID against registry.json; exit 2 if the theme ID is not found (exit 1 is reserved for system-level errors such as registry file not found or malformed)

### P5 — Build Pipeline v2

- **FR-240:** Build pipeline has 5 named steps: PARSE, ANALYZE, COMPOSE, RENDER, INLINE
- **FR-241:** PARSE: reads `slides.md`, extracts YAML frontmatter, splits on `---`, creates `SlideAST[]` list
- **FR-242:** ANALYZE: for each slide, resolves layout (explicit `@layout` tag or inferred), extracts context dict
- **FR-243:** COMPOSE: renders each slide using its Jinja2 layout template with context; produces HTML fragment list
- **FR-244:** RENDER: assembles the full Reveal.js HTML document with theme CSS and layout CSS
- **FR-245:** INLINE: embeds all CSS, JS, reveal.js vendor, fonts, and images as inline `<style>`/`<script>`/data URIs; raises `InlineError` if any external URL would be emitted
- **FR-246:** Layout inference in ANALYZE detects stat patterns (number + `%`/unit), quote patterns (long quoted text), list patterns (multiple bullet items), image paths
- **FR-247:** Each step logs at INFO level on start and DEBUG level for per-slide details
- **FR-248:** Unknown layouts fall back to `content` layout with a WARNING log
- **FR-249:** `--dry-run` skips file write at INLINE step; logs planned byte count

### P6 — Serve with Hot Reload

- **FR-250:** `aio serve {input}` starts an HTTP server with Starlette (minimal ASGI); binds to `127.0.0.1` by default; accepts `--host` flag (e.g., `--host 0.0.0.0`) to override the bind address
- **FR-251:** Server serves the built presentation at `GET /`
- **FR-252:** SSE endpoint at `/__sse__` (using `text/event-stream`) sends a `reload` event when source changes; Starlette `EventSourceResponse` implementation
- **FR-253:** Watchdog monitors `slides.md` and `.aio/config.yaml` for changes; triggers rebuild + notify
- **FR-254:** Rebuild on change completes in under 2 seconds for ≤ 30 slides
- **FR-255:** Port collision is detected before bind; exits with code 2 and a descriptive error
- **FR-256:** Graceful shutdown on SIGINT: socket closed, watchdog stopped, exit code 0
- **FR-257:** Injected JS snippet in the served HTML connects via `EventSource('/__sse__')` and calls `location.reload()` on message event; no WebSocket dependency required

---

## Success Criteria

### P1 Layouts
- **SC-200:** Each of 8 layouts renders in under 10ms per layout (unit benchmark)
- **SC-201:** HTML output validates as well-formed (no unclosed tags, correct nesting)
- **SC-202:** Each layout renders without a theme (basic but legible: black text, white background)
- **SC-203:** Images in `split-image-text` are base64-inlined with file size ≤ 3 MB
- **SC-204:** `hero-title` heading is legible on mobile (font scales via CSS media query)
- **SC-205:** `aio build` with all 8 layouts completes in under 30 seconds for a 30-slide deck

### P2 Themes
- **SC-210:** `aio theme list` shows ≥ 64 themes in under 1 second
- **SC-211:** Each imported theme has valid `DESIGN.md`, `theme.css`, `layout.css`
- **SC-212:** Import script completes in under 2 minutes including network calls
- **SC-213:** Theme `stripe` renders all 8 layouts with correct colors and fonts
- **SC-214:** `aio theme info stripe` returns full metadata without error
- **SC-215:** Nightly sync does not break builds from previous releases (backward compatible)

### P3 DESIGN.md
- **SC-220:** `extract.py` parses a real awesome-design-md DESIGN.md without error
- **SC-221:** Generated `theme.css` is valid CSS (no syntax errors)
- **SC-222:** Color variables in `theme.css` match hex values in DESIGN.md section 2
- **SC-223:** Layout Components section generates ≥ 8 `.layout-*` classes in `layout.css`
- **SC-224:** Missing section → WARNING logged, build continues with defaults

### P4 Theme CLI
- **SC-230:** `aio theme list` shows ≥ 64 rows in under 1 second
- **SC-231:** `aio theme info stripe` outputs full metadata in under 200ms
- **SC-232:** `aio theme use stripe` updates `config.yaml` within 100ms
- **SC-233:** `aio theme search "design"` returns ≥ 40 themes via fuzzy match
- **SC-234:** `aio theme create custom --from stripe` creates a ready-to-edit theme directory
- **SC-235:** All `--json` outputs parse as valid JSON (`json.loads()` succeeds)

### P5 Build Pipeline
- **SC-240:** Full build of 30 slides completes in under 30 seconds
- **SC-241:** Output HTML contains no external `https://` URLs (Art. II compliance)
- **SC-242:** Each step logs at the correct level (INFO for start, DEBUG for per-slide)
- **SC-243:** Unknown layout triggers WARNING and falls back to `content`; build exits 0
- **SC-244:** `--dry-run` produces no output file; prints planned byte count

### P6 Serve
- **SC-250:** Server starts in under 2 seconds and serves HTTP 200 at `/`
- **SC-251:** Reload event delivered to browser within 2 seconds of file change
- **SC-252:** Port collision detected and reported before bind; clean exit code 2
- **SC-253:** Graceful SIGINT shutdown completes in under 3 seconds

---

## Edge Cases & Error Handling

- **Empty slides.md**: Build exits with a clear `ParseError: No slides found` (not a Python traceback)
- **Unknown theme at build time**: Warning logged, falls back to `minimal` theme; build continues
- **Image file missing for split-image-text**: Warning logged; an SVG placeholder is substituted; build continues
- **All 64 themes missing (fresh install before import)**: `aio theme list` shows the `minimal` fallback; `aio init` works with `--theme minimal`
- **DESIGN.md section out of order**: Parser matches by heading text, not position; order is irrelevant
- **Concurrent serve + build**: File watcher handles multiple rapid saves by debouncing (100ms window)
- **Non-UTF-8 slides.md**: `ParseError` with encoding hint in message
- **`aio theme use` without a `.aio/` directory**: Exit 1 with message `Not inside an AIO project (no .aio/ found)`

---

## Constraints

- **Art. I** (Python 3.12+): All new code targets Python 3.12+; no `typing.Union[A, B]` or Python 3.9 compatibility shims
- **Art. II** (Offline HTML): Output HTML must pass the external-URL checker; any violation is a build failure
- **Art. III** (Visual Intelligence): All slides pass through `CompositionEngine.infer_layout()` even in v2 pipeline
- **Art. V** (DESIGN.md): `extract.py` parser must handle all 11 sections; breaking the format is a constitution violation
- **Art. VII** (Minimal deps): No new core dependencies beyond the 9 listed; `[enrich]` extras only for optional features
- **Art. VIII** (Reveal.js 5.x): The vendor bundle stays at 5.x; `</script>` is escaped in all inlined JS
- **Art. IX** (TDD, 80% coverage): Tests written before implementation; coverage gate enforced in CI
- **Art. X** (64+ themes): All themes must pass `aio theme validate`; no broken imports
