# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AIO** is an AI-native CLI toolkit that converts Markdown files into fully self-contained,
offline-capable HTML presentations (powered by Reveal.js 5.x). Visual Intelligence — automatic
layout inference, SVG charts, SVG composites, and AI image generation — is the core differentiator.

The constitution governing all technical decisions lives at `.specify/memory/constitution.md`.
**Read it before making architectural decisions.** Every PR has a Constitution Check gate.

---

## Commands

```bash
# Install for development
pip install -e ".[dev]"               # core + dev/test deps
pip install -e ".[enrich]"            # adds pillow, bs4, lxml, cssutils

# Lint and type-check
ruff check src/ tests/
ruff format src/ tests/
mypy src/aio/

# Tests
pytest tests/unit/ -v                          # fast unit tests only
pytest tests/integration/ -v                   # full pipeline tests
pytest --cov=src/aio --cov-report=term-missing # coverage (must be ≥ 80%)
pytest -k "test_infer_title_layout" -v         # single test by name

# CLI (after pip install -e .)
aio init my-deck --theme minimal
aio build slides.md -o out.html
aio build slides.md -o out.html --enrich       # with image generation
aio serve slides.md --port 3000
aio theme list
aio theme validate minimal
aio extract https://stripe.com -o DESIGN.md

# Check for external URL leaks in output HTML (Art. II compliance)
python -c "
import re, sys
html = open(sys.argv[1]).read()
bad = re.findall(r'(?:href|src)=[\"\'](https?://[^\"\']+)[\"\'']', html)
print('FAIL:', bad) if bad else print('PASS')
" out.html
```

---

## Architecture

### Build Pipeline (5 steps, `src/aio/commands/build.py`)

```
Markdown file
    │
    ▼ Step 1: parse_slides()    — mistune AST + yaml.safe_load() frontmatter → SlideAST[]
    ▼ Step 2: analyze_slides()  — CompositionEngine.infer_layout() → SlideRenderContext[]
    ▼ Step 3: compose_slides()  — Jinja2 layout templates → ComposedSlide[] (HTML fragments)
    ▼ Step 4: render_document() — assemble Reveal.js HTML + inline CSS/JS → full HTML string
    ▼ Step 5: inline_assets()   — verify no external URLs; append SSE snippet (serve mode)
                                 ← FAILS HERE (exit 3) if any external URL detected
```

### Module Map

| Module | Responsibility |
|--------|---------------|
| `src/aio/cli.py` | Typer root — **NO** `from __future__ import annotations` |
| `src/aio/commands/build.py` | 5-step pipeline: `parse_slides`, `analyze_slides`, `compose_slides`, `render_document`, `inline_assets` + `BuildResult` |
| `src/aio/commands/serve.py` | Starlette ASGI + SSE hot-reload + watchdog — **NO** `from __future__ import annotations` |
| `src/aio/commands/theme.py` | `theme list/search/info/use/show/create/validate` subcommands |
| `src/aio/commands/init.py` | `aio init` — scaffold `.aio/` project directory |
| `src/aio/composition/engine.py` | `CompositionEngine`: `infer_layout()`, `apply_layout()`, `sanitize_svg()` |
| `src/aio/composition/layouts.py` | 8 M1 layout types (LayoutType enum) |
| `src/aio/composition/metadata.py` | `SlideAST`, `SlideRenderContext`, `ComposedSlide`, `BuildResult`, `HotReloadEvent` |
| `src/aio/layouts/` | Jinja2 layout templates (`*.j2`) + `registry.py` (LayoutRegistry) |
| `src/aio/themes/loader.py` | `ThemeRecord` + `load_registry()` |
| `src/aio/themes/parser.py` | `parse_design_md()` — 11-section DESIGN.md parser |
| `src/aio/vendor/revealjs/` | Static Reveal.js 5.x UMD build (never update to v6) |
| `src/aio/_log.py` | Structured stderr logging — **use this, never `print()`** |
| `src/aio/_utils.py` | `build_jinja_env`, `base64_inline`, `escape_script`, `find_aio_dir` |
| `src/aio/_validators.py` | `yaml.safe_load()` wrapper, external-URL checker (`check_external_urls`) |
| `src/aio/exceptions.py` | `AIOError`, `ExternalURLError`, `ParseError`, `ThemeValidationError` |

### Key Paths

- Agent command prompts: `src/aio/agent_commands/{agent}/v{N}/` (frozen at release — add new version dir, never edit existing)
- Theme directory: `src/aio/themes/{id}/` with `DESIGN.md`, `theme.css`, `layout.css`, `meta.json`, `fonts/`
- Global theme registry: `src/aio/themes/registry.json`
- Per-project config: `.aio/config.yaml`, `.aio/meta.json`, `.aio/themes/registry.json`

---

## Non-Negotiable Rules (from Constitution)

1. **All imports MUST be absolute** — no relative imports anywhere (required for 4 distribution modes)
2. **`yaml.safe_load()` only** — never `yaml.load()` (prevents RCE via frontmatter)
3. **No external URLs in output HTML** — build step 4 checks and fails with exit code 3
4. **No `print()` in production code** — use `src/aio/_log.py` exclusively; stdout is reserved for piping
5. **Reveal.js pinned to 5.x** — never import or reference v6; check new vendor files for bare `import`/`export`; escape `</script>` → `<\/script>`
6. **`cli.py` and `serve.py` must NOT have `from __future__ import annotations`** — breaks Typer's runtime type introspection
7. **SVG output must not contain `<script>` tags** — sanitize all SVG before inlining
8. **No `unittest.mock` for the core pipeline** (init, build, compose, enrich) — use real temp directories

---

## Testing Conventions

```
tests/unit/        → isolated functions, mock I/O allowed
tests/integration/ → real temp dirs, full pipeline, no mocks for core pipeline
tests/visual/      → HTML snapshot comparison, SVG well-formedness
tests/fixtures/    → shared sample slides, themes, expected outputs, mock API responses
```

Coverage gate: **80% line, 75% branch**. CI blocks merge if below threshold.

TDD is mandatory: write tests first, confirm they fail, then implement.

---

## Dependency Rules

| Category | Allowed | Forbidden |
|----------|---------|-----------|
| Core | 9 deps listed in `pyproject.toml [project.dependencies]` | Django, numpy, pandas, tensorflow, any ORM |
| Enrich | pillow, beautifulsoup4, lxml, cssutils | Any web framework beyond minimal ASGI |
| Web in serve | Starlette (minimal ASGI) | Flask, FastAPI, Django |
| Charts | Pure Python SVG generation | D3.js, Chart.js, matplotlib, plotly |

Environment size: core < 150 MB, with enrich < 250 MB.

---

## DESIGN.md Schema (11 Sections — Mandatory)

Every theme's `DESIGN.md` must have all 11 sections for `extract.py` parsing and agent prompts:

1. Visual Theme
2. Color Palette (hex values + roles)
3. Typography
4. Components
5. Layout System
6. Depth & Shadows
7. Do's & Don'ts
8. Responsive Behavior
9. Animation & Transitions
10. Accessibility (WCAG 2.1 AA)
11. Agent Prompt Snippet (~200 words)

Validate with: `aio theme validate {id}`

---

## Performance Targets

| Operation | Target |
|-----------|--------|
| Build — 30 slides | < 30s |
| Serve hot-reload | < 2s |
| Markdown parse — 100 slides | < 500ms |
| New code regression | must not exceed baseline by > 5% |

---

## Specs & Planning Artifacts

Full implementation plan, data model, CLI contracts, and quickstart guide:

```
specs/main/
├── plan.md          — M0–M4 phase plan + constitution check table
├── research.md      — Technology decision log
├── data-model.md    — All core entities (SlideAST, ThemeRecord, ChartData, etc.)
├── quickstart.md    — Dev setup + workflow recipes
└── contracts/
    └── cli-contract.md  — Full CLI command contracts (args, options, exit codes, stdout/stderr)
```

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

## Active Technologies (M0)
- **Runtime**: Python 3.12+ (primary; 3.10+ tolerated)
- **Core deps**: typer 0.12.0, jinja2 3.1.2, mistune 3.0.2, pyyaml 6.0.1, rich 13.7.0, click 8.1.7
- **Storage**: Local filesystem — `.aio/` config dir, `~/.aio/logs/`
