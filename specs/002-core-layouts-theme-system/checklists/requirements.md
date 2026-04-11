# Requirements Checklist — 002-core-layouts-theme-system

## P1 — 8 Core Layouts

- [ ] FR-200: 8 Jinja2 layout templates defined in `src/aio/layouts/`
- [ ] FR-201: Each layout uses `{% block %}` syntax with fallback defaults
- [ ] FR-202: All layouts inherit `base.j2` Reveal.js structure
- [ ] FR-203: CSS class `.layout-{name}` injected on each `<section>`
- [ ] FR-204: Images in `split-image-text` are base64-inlined (max 3 MB)
- [ ] FR-205: Layout registry auto-discovered by scanning `.j2` files
- [ ] FR-206: Each layout supports 0–10 metadata blocks with defaults
- [ ] FR-207: Markdown in layout blocks rendered via mistune
- [ ] FR-208: Layout CSS scoped to `.layout-{name}` (no cross-layout leakage)

## P2 — Theme System (64+ Themes)

- [ ] FR-210: Global `src/aio/themes/registry.json` with ≥ 64 theme entries
- [ ] FR-211: Each theme has `src/aio/themes/{id}/` with DESIGN.md, theme.css, layout.css, meta.json
- [ ] FR-212: All DESIGN.md files have 11 mandatory sections
- [ ] FR-213: `theme.css` defines `--color-*` and `--font-*` CSS custom properties
- [ ] FR-214: `layout.css` defines `.layout-{name}` theme-specific overrides
- [ ] FR-215: `meta.json` has id, name, colors, typography, categories, author, source_url
- [ ] FR-216: `scripts/import-awesome-designs.py` imports ≥ 64 themes from awesome-design-md
- [ ] FR-217: Nightly GitHub Actions workflow `3-sync-themes.yml` runs import script
- [ ] FR-218: Project `.aio/themes/registry.json` contains only the selected theme
- [ ] FR-219: `aio theme use {id}` updates config.yaml within 100ms

## P3 — DESIGN.md 11-Section Format

- [ ] FR-220: DESIGN.md has 11 required sections (Visual Theme through Agent Prompt Snippet)
- [ ] FR-221: `extract.py` matches sections by number or heading text
- [ ] FR-222: Color Palette parsed into meta.json colors object and `--color-*` vars
- [ ] FR-223: Typography parsed into `--font-*` CSS vars
- [ ] FR-224: Components section generates skeleton `.layout-*` CSS classes
- [ ] FR-225: Layout System populates `layout.css` template-specific overrides
- [ ] FR-226: Missing sections produce WARNING; parsing continues with defaults
- [ ] FR-227: DESIGN.md remains human-readable markdown

## P4 — Theme CLI

- [ ] FR-230: `aio theme` group has 6 subcommands: list, search, info, use, show, create
- [ ] FR-231: `aio theme list` with `--limit`, `--filter`, `--search` options and rich table output
- [ ] FR-232: `aio theme info {id} [--json]` shows full metadata
- [ ] FR-233: `aio theme use {id}` validates theme and updates config + registry
- [ ] FR-234: `aio theme show {id} [--section N] [--all]` outputs DESIGN.md
- [ ] FR-235: `aio theme create {name} [--from id]` scaffolds new theme
- [ ] FR-236: `aio theme search` uses fuzzy matching (difflib or Levenshtein)
- [ ] FR-237: `--filter` supports comma-separated tags
- [ ] FR-238: `--json` flag on list, info, search; output is valid JSON
- [ ] FR-239: All subcommands validate theme ID; exit 1 if unknown

## P5 — Build Pipeline v2

- [ ] FR-240: Pipeline has 5 named steps: PARSE, ANALYZE, COMPOSE, RENDER, INLINE
- [ ] FR-241: PARSE reads slides.md, extracts frontmatter and slide blocks
- [ ] FR-242: ANALYZE resolves layout per slide (explicit or inferred)
- [ ] FR-243: COMPOSE renders each slide via Jinja2 layout with context dict
- [ ] FR-244: RENDER assembles full Reveal.js HTML document with theme CSS
- [ ] FR-245: INLINE embeds all CSS, JS, fonts, images; raises InlineError on external URL
- [ ] FR-246: Layout inference detects stat, quote, list, and image patterns
- [ ] FR-247: Each step logs at INFO (start) and DEBUG (per-slide) level
- [ ] FR-248: Unknown layouts fall back to `content` with WARNING
- [ ] FR-249: `--dry-run` skips file write; logs planned byte count

## P6 — Serve with Hot Reload

- [ ] FR-250: `aio serve` starts Starlette ASGI server
- [ ] FR-251: `GET /` returns 200 with full presentation HTML
- [ ] FR-252: SSE/WebSocket endpoint at `/_aio/reload`
- [ ] FR-253: Watchdog monitors slides.md and .aio/config.yaml; triggers rebuild
- [ ] FR-254: Rebuild on change completes in under 2 seconds for ≤ 30 slides
- [ ] FR-255: Port collision detected before bind; exit 1 with descriptive error
- [ ] FR-256: Graceful SIGINT shutdown: socket closed, watchdog stopped, exit 0
- [ ] FR-257: Injected JS auto-connects to `/_aio/reload` and calls `location.reload()`
