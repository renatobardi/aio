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

# Browse available themes (57 themes)
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

57 themes modelled after real product design systems: `stripe`, `linear-app`, `vercel`, `notion`, `figma`, `cursor`, `supabase`, `airbnb`, and more.

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

## Image Enrichment & Caching

When you build with `--enrich`, AIO automatically generates images for slides using a multi-provider fallback:

1. **Pollinations** (free, no API key) — <8s per image
2. **OpenAI DALL-E** (paid, $0.08–0.12/image, requires `OPENAI_API_KEY`)
3. **Unsplash** (free, requires `UNSPLASH_API_KEY`)
4. **SVG fallback** (free, automatic) — <500ms

All images are cached locally in `.aio/cache/images/` and reused on rebuilds for 95% faster build times.

```bash
# First build: generates and caches images (~20–30s)
aio build slides.md --enrich

# Second build: cache hits, only re-renders (~2s)
aio build slides.md --enrich

# Check cache stats
aio build slides.md --cache-stats
# Output:
#   Entries: 10
#   Size: 12.3 MB / 100.0 MB
#   AIO version: 0.1.0

# Clear cache if needed
aio build slides.md --cache-clear
```

**Cache Management**:
- **Automatic**: Cache is created and managed automatically (`.aio/cache/`)
- **LRU Eviction**: When cache > 100 MB, oldest entries deleted until < 50 MB
- **Version-locked**: Cache invalidates if AIO version changes
- **Per-provider keys**: Same prompt on different providers = different cache entries

See `docs/image-generation-troubleshooting.md` for debugging and `specs/004-svg-composites-api/quickstart.md` for detailed usage.

---

## Development

```bash
ruff check src/ tests/ && ruff format src/ tests/
mypy src/aio/
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest --cov=src/aio --cov-report=term-missing   # CI gate: ≥ 20%; aspirational target: 80%
pytest -k "test_infer_title_layout" -v            # single test
```

---

## Milestones

| Milestone | Status |
|-----------|--------|
| M0 — CLI, parser, config, logging | Complete |
| M1 — Layouts, themes, build, serve | Complete |
| M2 — SVG charts, icons, extract, 57 themes | Complete |
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
