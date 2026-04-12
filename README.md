# aio

AI-native CLI toolkit that converts Markdown files into fully self-contained, offline-capable HTML presentations powered by Reveal.js 5.x.

**Visual Intelligence** — automatic layout inference, SVG charts, icon library, and AI image generation — is the core differentiator. Output is a single HTML file with zero external dependencies.

---

## Install

```bash
pip install -e ".[dev]"       # core + dev/test deps
pip install -e ".[enrich]"    # adds pillow, bs4, lxml, cssutils (for extract + image enrichment)
```

Requires Python 3.12+. Core environment < 150 MB.

---

## Usage

```bash
# Start a new presentation
aio init my-deck --theme minimal

# Build to a standalone HTML file
aio build slides.md -o out.html

# Build with AI image enrichment (requires [enrich])
aio build slides.md -o out.html --enrich

# Serve with hot-reload
aio serve slides.md --port 3000

# Browse available themes (58 themes)
aio theme list
aio theme info stripe

# Validate a theme's DESIGN.md
aio theme validate minimal

# Scrape a design site into a DESIGN.md (requires [enrich])
aio extract https://stripe.com -o DESIGN.md

# Show AI agent prompts
aio commands --agent claude
```

---

## How it works

The build pipeline runs 5 steps:

1. **parse** — Markdown + YAML frontmatter → `SlideAST[]`
2. **analyze** — `CompositionEngine.infer_layout()` → `SlideRenderContext[]`
3. **compose** — Jinja2 layout templates + SVG chart injection → `ComposedSlide[]`
4. **render** — Assemble Reveal.js HTML with inlined CSS/JS
5. **inline** — Verify no external URLs; append SSE snippet in serve mode *(exits 3 on violation)*

---

## Themes

58 themes modelled after real product design systems: `stripe`, `linear-app`, `vercel`, `notion`, `figma`, `cursor`, `supabase`, `airbnb`, and more.

Each theme ships with `DESIGN.md` (11-section design spec), `theme.css`, `layout.css`, and `meta.json`.

```bash
aio theme list
aio theme validate <id>
```

New themes sync nightly from [awesome-design-md](https://github.com/HU-UH/awesome-design-md) via `.github/workflows/3-sync-themes.yml`.

---

## Visuals

| Feature | Module |
|---------|--------|
| 5 chart types (Bar, Line, Pie, Scatter, Heatmap) | `visuals/dataviz/charts.py` |
| CSV / JSON / dict data ingestion | `visuals/dataviz/data_parser.py` |
| 159 Lucide icons | `visuals/svg/icons.py` |
| SVG composites (flowcharts, org charts) | `visuals/svg/composites.py` *(M2.5 — stub)* |

All SVG is generated in pure Python — no D3, no Chart.js, no external assets.

---

## Development

```bash
ruff check src/ tests/ && ruff format src/ tests/
mypy src/aio/
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest --cov=src/aio --cov-report=term-missing   # target ≥ 80%
pytest -k "test_infer_title_layout" -v            # single test
```

---

## Milestones

| Milestone | Status |
|-----------|--------|
| M0 — CLI, parser, config, logging | Complete (99.4%) |
| M1 — Layouts, themes, build, serve | Complete (100%) |
| M2 — SVG charts, icons, extract, 58 themes | Complete |
| M2.5 — SVG composites, AI image gen, 8 agents | Pending |
| M3 — Coverage gates, perf hardening | Pending |
| M4 — 4 distribution modes, 64+ themes | Pending |

---

## Specs

```
specs/main/
├── plan.md           — M0–M4 phase plan + constitution check table
├── research.md       — Technology decision log
├── data-model.md     — Core entities (SlideAST, ThemeRecord, ChartData…)
├── quickstart.md     — Dev setup + workflow recipes
└── contracts/
    └── cli-contract.md  — Full CLI contracts (args, options, exit codes)
```
