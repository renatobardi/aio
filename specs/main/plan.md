# Implementation Plan: AIO — AI-Native Presentation Generator

**Branch**: `main` | **Date**: 2026-04-11 | **Spec**: Project constitution at `.specify/memory/constitution.md`
**Input**: Architectural constitution + full implementation plan provided at project inception

## Summary

AIO is a Python CLI toolkit that generates fully self-contained, offline-capable HTML presentations
from Markdown input, using Reveal.js 5.x for rendering. Visual Intelligence (automatic layout
inference, SVG composites, data visualization, AI image generation) is the core differentiator.
The project is greenfield, targeting v0.1.0 over 12 weeks (M0–M4), with 8 AI agent integrations,
64+ themes, and 4 distribution modes (zero-install, zipapp, PyInstaller, pip).

## Technical Context

**Language/Version**: Python 3.12+ (primary target; 3.10+ tolerated for extended support)
**Primary Dependencies**: typer 0.12, jinja2 3.1, mistune 3.0, pyyaml 6.0, pygments 2.17,
watchdog 3.0, httpx 0.26, rich 13.7, click 8.1 (core); pillow 10.1, beautifulsoup4 4.12,
lxml 4.9, cssutils 2.10 (optional `[enrich]`/`[extract]`)
**Storage**: Local filesystem only; `.aio/` project dir + `~/.aio/` user home
**Testing**: pytest 7.4 + pytest-cov + pytest-asyncio + pytest-httpx; mypy 1.7; ruff 0.1
**Target Platform**: Windows, macOS, Linux (cross-platform CI/CD)
**Project Type**: CLI tool + library (4 distribution modes: zero-install, zipapp, exe, pip)
**Performance Goals**: Build 30 slides < 30s; serve hot-reload < 2s; markdown parse < 500ms for 100 slides
**Constraints**: Offline-first output; environment < 150 MB (core) / < 250 MB (enrich); no CDN deps
**Scale/Scope**: Single-user local tool; 64+ themes; 8 AI agents; outputs 2–5 MB HTML per presentation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Article | Validation | Target Milestone |
|------|---------|------------|-----------------|
| Python 3.12+ syntax allowed | Art. I | `python --version >= 3.12`; walrus/unions/match used freely | Pre-M0 |
| Output is offline standalone HTML | Art. II | Build fails on external URL detection; offline test passes | M0 partial → M1 full |
| Composition Engine is foundational | Art. III | `CompositionEngine` class exists; all 16 layout stubs present | M0 |
| 8 AI agents supported | Art. IV | 8 `agent_commands/` dirs with v1 templates | M2.5 |
| DESIGN.md 11-section schema enforced | Art. V | JSON schema defined; `extract.py` parser validates | M1 |
| Image generation free by default | Art. VI | Pollinations.ai works without API key; SVG fallback on failure | M2.5 |
| Core deps < 150 MB | Art. VII | `pip install -e .` measured < 150 MB | M0 |
| Reveal.js pinned to 5.x | Art. VIII | `reveal.js >= 5.0.0, < 6.0` vendored; UMD builds; `</script>` escaped | M1 |
| 80% line + 75% branch coverage | Art. IX | `pytest --cov=src/aio` reports 80%+ in CI | M3 |
| 64+ themes in registry | Art. X | `aio theme list` shows 64+; nightly sync active | M4 |
| Agent commands versioned + frozen | Art. XI | Prompts in `agent_commands/{agent}/v{N}/`; no live fetch | M2.5 |
| 4 distribution modes tested in CI | Art. XII | zero-install, .pyz, .exe/.bin, pip all tested cross-platform | M4 |

**Constitution Check Result (Phase 0):** ✅ All gates achievable; no violations requiring justification at inception.

## Project Structure

### Documentation (this plan)

```text
specs/main/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI contracts)
└── tasks.md             # /speckit.tasks output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/aio/
├── __init__.py                    # version = "0.1.0"
├── __main__.py                    # python -m aio entry point
├── cli.py                         # Typer root — NO from __future__ annotations
│
├── composition/
│   ├── engine.py                  # CompositionEngine (infer_layout, apply_layout, validate_structure)
│   ├── layouts.py                 # 16 Layout classes (Title → Interactive)
│   ├── metadata.py                # SlideMetadata, NoteMetadata, TimingMetadata, AnimationMetadata
│   └── templates/                 # Per-layout Jinja2 .j2 files + reveal.html.j2 root
│
├── visuals/
│   ├── svg/
│   │   ├── composites.py          # SVGComposite engine (render_chart_bg, render_decoration, render_illustration)
│   │   └── icons.py               # Lucide icon registry + render_icon (~200 icons)
│   ├── dataviz/
│   │   ├── charts.py              # BarChart, LineChart, PieChart, ScatterChart, HeatmapChart → SVG
│   │   └── data_parser.py         # CSV/JSON/dict → internal data model
│   └── enrichment.py              # PollinationsAI (default), DALL-E, Midjourney, StableDiffusion stubs
│
├── commands/
│   ├── init.py                    # Scaffold .aio/ project
│   ├── build.py                   # 4-step pipeline: parse → resolve → render → inline
│   ├── serve.py                   # HTTP server + watchdog hot reload
│   ├── theme.py                   # theme list / info / validate
│   ├── extract.py                 # Web scrape → DESIGN.md
│   └── enrich.py                  # --enrich flag orchestration
│
├── agents/
│   └── prompts.py                 # load_agent_template(agent, phase, version) + list_agents()
│
├── agent_commands/                # Vendored, frozen per release
│   ├── claude/v1/{SYSTEM,INIT_PHASE,COMPOSITION_PHASE,ENRICH_PHASE,REFINEMENT_PHASE}.md
│   ├── gemini/v1/
│   ├── copilot/v1/
│   ├── windsurf/v1/
│   ├── devin/v1/
│   ├── chatgpt/v1/
│   ├── cursor/v1/
│   └── generic/v1/
│
├── themes/
│   ├── registry.json              # Global registry (64+ entries)
│   ├── loader.py                  # Theme loading + path resolution
│   ├── validator.py               # JSON schema validation of DESIGN.md
│   ├── minimal/{DESIGN.md,theme.css,layout.css,meta.json,fonts/}
│   ├── modern/
│   ├── vibrant/
│   └── ... (61+ more)
│
├── vendor/
│   ├── revealjs/dist/             # reveal.min.js, reveal.css, plugins (UMD, escaped)
│   └── lucide/icons.json          # Icon metadata
│
├── _tpl.py                        # Jinja2 env, filters (escape_html, slugify, highlight_code)
├── _log.py                        # Structured stderr logging
├── _http.py                       # httpx lazy-import wrapper
├── _validators.py                 # YAML safe_load, JSON schema, HTML external-URL check
└── _utils.py                      # slugify, escape, format helpers

tests/
├── conftest.py
├── unit/                          # Isolated functions, mocked I/O
├── integration/                   # Full pipeline, real temp dirs
├── visual/                        # HTML snapshots, SVG validation, responsive checks
└── fixtures/                      # sample_slides.md, themes, expected_output.html, mock agent responses

scripts/
├── import-awesome-designs.py      # Sync awesome-design-md (--from-local flag)
├── validate-themes.py             # Offline validation
└── measure-bundle-size.py         # Track HTML output size

examples/
├── quick-start-5-slides.md
├── enterprise-50-slides.md
└── rich-visuals-art-direction.md

docs/
├── ARCHITECTURE.md
├── theme-system.md                # DESIGN.md 11-section spec
├── agent-prompts.md
├── dataviz.md
├── composition-engine.md
└── deployment.md

.github/workflows/
├── 1-lint-test.yml                # ruff, mypy, pytest (PR + push main)
├── 2-build-dist.yml               # PyInstaller + zipapp + PyPI (on tag)
└── 3-sync-themes.yml              # Nightly awesome-design-md sync
```

**Structure Decision**: Single Python package (`src/aio/`) with domain-separated submodules.
Composition, visuals, commands, and agents are top-level subpackages. No relative imports anywhere.
All 4 distribution modes require absolute imports, which this structure enforces.

## Complexity Tracking

> *No constitution violations at plan inception — table intentionally empty.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| — | — | — |

---

## Phase 0 — Foundation Research

### Research Outcomes

All technical choices are fully specified in the user-provided plan. No NEEDS CLARIFICATION remain.
The research.md below consolidates decisions and rationale.

---

## Phase Plans (M0–M4)

### M0 — Foundation (Weeks 1–2)

**Objective:** Buildable repo, CI/CD green, CLI skeleton, composition engine stub, 3 base themes.

**Deliverables:**
1. `src/aio/` scaffold (8 core files: `__init__`, `__main__`, `cli`, `_log`, `_http`, `_validators`, `_utils`, `_tpl`)
2. Typer CLI root with subcommands: `init`, `build`, `serve`, `theme`, `extract` (all stubbed)
3. `pyproject.toml` with all 9 core deps pinned
4. 3 GitHub Actions workflows (`1-lint-test.yml`, `2-build-dist.yml`, `3-sync-themes.yml`)
5. `CompositionEngine` class skeleton with `infer_layout()` stub
6. 3 base themes (`minimal`, `modern`, `vibrant`) with 9-section DESIGN.md skeletons
7. `src/aio/themes/registry.json` (3 entries)
8. Pytest setup: `tests/conftest.py`, `tests/unit/test_cli_basics.py` (5+ smoke tests)
9. `CONSTITUTION.md` at repo root linking to `.specify/memory/constitution.md`

**Coverage target:** 20%
**Go/No-Go:** `pip install -e .` < 150 MB; GitHub Actions green; `aio --help` works; 3 themes loadable.

---

### M1 — Core Layouts (Weeks 3–4)

**Objective:** 8 core layouts fully implemented, layout inference engine, Reveal.js 5.x vendored, offline HTML output.

**Deliverables:**
1. 16 Layout classes in `src/aio/composition/layouts.py` (8 fully implemented + 8 stubs)
2. `CompositionEngine.infer_layout()` with heuristic scoring (>80% accuracy on common patterns)
3. Jinja2 templates: `reveal.html.j2` + 8 per-layout `.j2` files
4. Reveal.js 5.0.0+ vendored to `src/aio/vendor/revealjs/dist/`; UMD validated; `</script>` escaped
5. 4-step build pipeline in `src/aio/commands/build.py`:
   - Step 1 (Parse): Markdown → AST + YAML frontmatter via `yaml.safe_load()`
   - Step 2 (Resolve): Theme load + CSS validation + settings merge
   - Step 3 (Render): Jinja2 per-slide render with theme vars
   - Step 4 (Inline): Embed all CSS + JS + reveal.js; external URL check must fail build if detected
6. `theme.py`: `aio theme list`, `aio theme info {id}`, `aio theme validate {id}`
7. Base themes updated to 11-section DESIGN.md format

**Tests:** `test_full_pipeline.py` (integration), `test_layout_inference.py` (20+ cases), `test_html_snapshots.py`
**Coverage target:** 50%
**Go/No-Go:** `aio init test && aio build slides.md -o out.html` produces single offline-capable HTML file.

---

### M2 — Visual Foundation (Weeks 5–6)

**Objective:** DataViz engine (SVG charts), Lucide icon library, SVG composites skeleton, full extract.py.

**Deliverables:**
1. `src/aio/visuals/dataviz/charts.py`: `BarChart`, `LineChart`, `PieChart`, `ScatterChart`, `HeatmapChart` → static SVG
2. `src/aio/visuals/dataviz/data_parser.py`: CSV inline / JSON / dict → internal data model
3. `src/aio/visuals/svg/icons.py`: ~200 Lucide icons, `render_icon(name, color, size)`, CSS color override
4. `src/aio/visuals/svg/composites.py`: `ChartBackground`, `Decoration`, `Illustration` stubs (full impl in M2.5)
5. `src/aio/commands/extract.py`: scrape design sites → DESIGN.md 11-section output (mock-tested)
6. Theme CSS validation via cssutils (WCAG contrast check, deprecated property warnings)
7. 3 base themes enhanced to full 11-section DESIGN.md with CSS + fonts

**Tests:** `test_dataviz_charts.py` (30+ cases), `test_icon_library.py` (20+ cases), `test_extract_awesome_designs.py`
**Coverage target:** 65%
**Go/No-Go:** Data slides render SVG charts; `aio extract {url}` produces valid DESIGN.md.

---

### M2.5 — Visual Richness (Week 7)

**Objective:** SVG Composites full implementation, Pollinations.ai integration, `--enrich` flag, all 8 agent templates.

**Deliverables:**
1. `src/aio/visuals/svg/composites.py` full: flowcharts, org charts, infographics; `{{ compose() }}` Jinja2 filter
2. `src/aio/visuals/enrichment.py`: `PollinationsAI` (default, async, no key); `DALLE`/`Midjourney`/`StableDiffusion` stubs
3. `src/aio/commands/enrich.py`: `aio enrich slides.md`; `--provider`; `--skip-existing`; SVG fallback
4. `aio build slides.md --enrich`: async image generation, non-blocking, base64 embed
5. `src/aio/agent_commands/{8 agents}/v1/`: all 5 phase files per agent (40 files total)
6. `src/aio/agents/prompts.py`: `load_agent_template(agent, phase, version='v1')`, `list_agents()`

**Tests:** `test_svg_composites.py` (15+ cases), `test_enrich_integration.py` (mock HTTP), `test_agent_prompts.py`
**Coverage target:** 75%
**Go/No-Go:** `aio enrich slides.md` generates + embeds images; `aio --agent claude` displays COMPOSITION_PHASE.md.

---

### M3 — Intelligent Composition (Weeks 8–9)

**Objective:** Agent prompts v2, refined layout inference, rich slide metadata, responsive design, enhanced serve.

**Deliverables:**
1. Agent prompt v2 for all 8 agents (`agent_commands/{agent}/v2/COMPOSITION_PHASE.md`)
2. `CompositionEngine.infer_layout()` refined to >80% accuracy; logged suggestions; `layout:` frontmatter override
3. `src/aio/composition/metadata.py`: `SlideMetadata`, `NoteMetadata`, `TimingMetadata`, `AnimationMetadata`
4. Frontmatter extensions: `timing: 2m`, `notes: "..."`, `transition: fade 500ms`
5. Mobile-first CSS + Reveal.js responsive plugin; 16:9 / 4:3 / 21:9 aspect ratio support
6. `src/aio/commands/serve.py`: `aio serve slides.md` → localhost:3000; hot reload < 2s; keyboard shortcuts

**Tests:** `test_auto_layout_v2.py`, `test_serve_hot_reload.py`, `test_responsive_layouts.py`
**Coverage target:** 80%+ (CI gate locks here)
**Go/No-Go:** Auto-layout selects correct layout ≥80% on test fixtures; serve hot-reloads in < 2s; speaker notes exportable.

---

### M4 — Polish & Release (Weeks 10–12)

**Objective:** 8 remaining layouts, animations, 64+ themes, Aurea migration, docs, v0.1.0 release.

**Deliverables:**
1. 8 additional layout classes fully implemented: `ComparisonSlide`, `GallerySlide`, `DataSlide`,
   `IconGridSlide`, `NarrativeSlide`, `DiagramSlide`, `CustomSlide`, `InteractiveSlide`
2. Reveal.js 5.x transition support via frontmatter (`transition: fade 500ms`, global theme defaults)
3. `src/aio/commands/migrate.py`: `aio migrate aurea_slides.md -o aio_slides.md` (Aurea → AIO YAML)
4. 64+ themes from awesome-design-md (nightly `3-sync-themes.yml` active; all themes smoke-tested)
5. Complete documentation (`README.md`, `CONTRIBUTING.md`, `docs/` — 6 guides)
6. Release automation: tag `vX.Y.Z` → GitHub Actions builds all 4 distributions → PyPI OIDC publish
7. 3 example projects in `examples/`
8. Performance + security audit: `pip-audit`, HTML sanitization, bundle size tracking

**Tests:** `test_all_themes.py` (64 smoke tests), `test_migration_aurea_to_aio.py`, `test_all_animations.py`
**Coverage target:** 80%+ maintained; all 4 distribution modes tested in CI matrix
**Go/No-Go:** v0.1.0 on PyPI; exe/bin downloadable; 50-slide example builds < 30s; 0 critical bugs.

---

## Phase Dependency Order

```
M0 (Foundation)
    ↓
M1 (Core Layouts + reveal.js + build pipeline)
    ↓
M2 (DataViz + Icons + extract.py)
    ↓
M2.5 (SVG Composites + Pollinations.ai + 8 agent templates)
    ↓
M3 (Intelligent Composition + serve v2)   ← 80% coverage gate locks here
    ↓
M4 (Polish + 64 themes + release)
    ↓
v0.1.0 🎉
```

**Phase prerequisites:**
- Before M1: Python 3.12+ env; repo structure; CI/CD green
- Before M2: Reveal.js vendored; 4-step build pipeline working end-to-end
- Before M2.5: DataViz + icons working; `agent_commands/` skeleton present
- Before M3: Image generation tested; all 8 agent templates complete
- Before M4: 80% coverage locked; serve hot-reload stable

---

## Performance Budget

| Metric | Target | Measurement Context |
|--------|--------|---------------------|
| Build — 30 slides | < 30s | i5, 8 GB RAM, local SSD |
| Serve hot-reload | < 2s | File change → reload complete |
| Markdown parse — 100 slides | < 500ms | In-process, no async |
| Image generation (Pollinations.ai) | async, non-blocking | Parallel with HTML render |
| HTML output size | 2–5 MB | 16-slide average presentation |
| Peak memory — build | < 500 MB | Measured at render step |

Regressions > 5% from baseline must be investigated before merge (`scripts/benchmark.py`).

---

## Complexity Budget

| Risk Level | Cyclomatic Complexity | Policy |
|------------|----------------------|--------|
| Low | < 5 | Default; no review required |
| Medium | 5–10 | Acceptable for pipeline orchestrators + layout inference |
| High | > 10 | Forbidden without 100% test coverage + explicit code review |

Module size limits: `build.py`/`serve.py` ≤ 1000 LOC; `composition/engine.py`/`dataviz/charts.py` ≤ 800 LOC; `_utils.py` ≤ 400 LOC.
