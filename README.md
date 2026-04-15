# 🎬 AIO — AI-Native Presentation Generator

AI-native CLI toolkit that converts Markdown files into fully self-contained, offline-capable HTML presentations powered by Reveal.js 5.x.

**Visual Intelligence** is our core differentiator:
- 🤖 **Automatic Layout Inference** — AI understands your content and chooses the best layout
- 📊 **SVG Charts** — 5 chart types (Bar, Line, Pie, Scatter, Heatmap) rendered in pure Python
- 🎨 **159 Built-in Icons** — Lucide icon library integrated
- 🖼️ **AI Image Generation** — Auto-generate images with Pollinations (free) or DALL-E (paid)
- 🎯 **57+ Themes** — Real product design systems (Stripe, Linear, Vercel, Figma, Notion, etc.)

**Output**: Single `.html` file with zero external dependencies. Works offline anywhere.

---

## Install

```bash
# Development setup
pip install -e ".[dev]"       # core + dev/test deps + pytest
pip install -e ".[enrich]"    # adds image generation + web scraping

# Just want to use it?
pip install aio
```

**Requirements**: Python 3.12+ | **Size**: Core < 150 MB, with enrich < 250 MB

---

## 🚀 Quick Start (5 minutes)

### 1. Create Your First Presentation

```bash
# Initialize a new project
aio init my-deck --theme minimal

# This creates:
# my-deck/
# ├── slides.md          ← Edit this file with your content
# ├── .aio/
# │   ├── config.yaml    ← Project settings
# │   └── cache/         ← Image cache (auto-managed)
```

### 2. Write Your Slides

Edit `my-deck/slides.md`:

```markdown
---
title: "My First Presentation"
subtitle: "Built with AIO"
theme: minimal
---

# Slide 1: Title

Your content here.

---

# Slide 2: With Chart

@chart-type: bar
@chart-data:
  labels: [Q1, Q2, Q3, Q4]
  values: [12, 19, 8, 15]

---

# Slide 3: With Icon

See all 159 Lucide icons in [@icon-name](https://lucide.dev)
```

### 3. Build & Preview

```bash
# Fast build (< 5s)
aio build slides.md -o out.html

# Live preview with hot-reload
aio serve slides.md --port 3000

# With AI image generation (first build ~30s, cached after)
aio build slides.md -o out.html --enrich
```

### 4. Choose a Theme

```bash
# Browse 57 themes (Stripe, Linear, Vercel, Figma, etc.)
aio theme list

# See theme details
aio theme info linear

# Use a theme
aio build slides.md --theme linear -o out.html
```

👉 **[Full Quickstart Guide →](docs/quickstart-first-presentation.md)**

---

## 📚 Common Commands

```bash
# Create & manage presentations
aio init my-deck --theme minimal          # New project
aio build slides.md -o out.html          # Build once
aio serve slides.md --port 3000          # Live preview

# Themes
aio theme list                            # Show all 57 themes
aio theme info stripe                     # Theme details
aio theme validate minimal                # Check DESIGN.md

# Image Generation (requires [enrich])
aio build slides.md --enrich              # Use Pollinations (free, default)
aio build slides.md --enrich --image-provider openai  # Use DALL-E (paid)
aio build slides.md --cache-stats         # Check image cache size
aio build slides.md --cache-clear         # Clear cache

# Web Scraping (requires [enrich])
aio extract https://stripe.com -o DESIGN.md  # Scrape design site

# Agent Templates
aio commands --agent claude               # Show Claude prompts
aio commands --agent gemini               # Show Gemini prompts
```

---

## 🏗️ How It Works

AIO's **build pipeline** runs 5 steps to transform Markdown into a standalone HTML presentation:

```
Markdown + YAML frontmatter
    ↓
1️⃣  Parse      → SlideAST (abstract syntax tree)
    ↓
2️⃣  Analyze    → CompositionEngine infers best layouts
    ↓
3️⃣  Compose    → Jinja2 templates + SVG charts
    ↓
4️⃣  Render     → Reveal.js HTML + inline CSS/JS
    ↓
5️⃣  Inline     → Embed all assets, verify no external URLs
    ↓
Single standalone .html file ✨
```

Each step is **testable, cacheable, and extensible**. No external dependencies.

👉 **[Architecture Deep Dive →](docs/architecture-overview.md)**

---

## 🎨 Themes (57+ Real Design Systems)

AIO ships with themes modeled after **real product design systems**:

**Tech/SaaS:** Linear, Stripe, Vercel, Figma, Cursor, Supabase, Clerk  
**Creative:** Dribble, Behance, Framer, Webflow  
**Premium:** Notion, Roam, Obsidian  
**Minimal:** Minimal, Zen, Stark  
**Corporate:** Corporate, Finance, Academic

Each theme includes:
- `DESIGN.md` — 11-section design spec (colors, typography, components, accessibility)
- `theme.css` — Color palette & typography
- `layout.css` — Layout-specific styles
- `meta.json` — Metadata

**Browse themes:**
```bash
aio theme list                    # List all 57+ themes
aio theme info linear            # Details + preview
aio theme validate linear        # Check DESIGN.md compliance
```

💡 New themes sync **nightly** from [awesome-design-md](https://github.com/HU-UH/awesome-design-md).

---

## 📊 Visual Features

| Feature | Example | Module |
|---------|---------|--------|
| **5 Chart Types** | Bar, Line, Pie, Scatter, Heatmap | `visuals/dataviz/charts.py` |
| **Data Formats** | CSV, JSON, inline dict | `visuals/dataviz/data_parser.py` |
| **Icon Library** | 159 Lucide icons | `visuals/svg/icons.py` |
| **SVG Composites** | Flowcharts, org charts, backgrounds | `visuals/svg/composites.py` |
| **Responsive SVG** | Auto-scales to viewport | Inline rendering |

**Example: Embed a Chart**

```markdown
# Revenue Trends

@chart-type: line
@chart-data:
  series:
    - name: "Q1-Q4 2024"
      values: [12000, 19000, 8000, 15000]
  labels: [Q1, Q2, Q3, Q4]
  title: "Quarterly Revenue"
```

**Example: Icon**

```markdown
# Features

- @check-circle Blue ✓ Feature A
- @trending-up Growth ↗ Feature B
- @lock Secure 🔒 Feature C
```

✨ All SVG is generated in **pure Python** — no D3, Chart.js, or external assets.

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

## 🛠️ Development

### Setup

```bash
git clone https://github.com/renatobardi/aio.git
cd aio

# Install dependencies
pip install -e ".[dev]"        # core + dev/test deps
pip install -e ".[enrich]"     # for extract + image enrichment

# Setup git hooks (code safety)
hapai install && hapai status
```

### Code Quality

```bash
# Lint & format
ruff check src/ tests/ && ruff format src/ tests/

# Type checking
mypy src/aio/

# Tests
pytest tests/unit/ -v                    # fast unit tests
pytest tests/integration/ -v             # full pipeline
pytest --cov=src/aio --cov-fail-under=20  # coverage gate: ≥ 20%
pytest -k "test_parse" -v                # single test
```

### Guardrails (Hapai)

This repo uses **hapai** — automated git hooks for code safety:

```bash
# After cloning, setup hapai (one-time)
hapai install
hapai status
```

**Hapai enforces:**
- ✅ Branch naming: `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`, `perf/`, etc.
- ✅ No direct commits to `main`
- ✅ No `.env` or lockfile edits
- ✅ No destructive commands
- ✅ Meaningful commit messages (no `Co-Authored-By`)

Before pushing:
```bash
ruff check src/ tests/ && mypy src/aio/ && pytest tests/ -v --cov=src/aio --cov-fail-under=20
```

👉 **[Full Contributing Guide →](CONTRIBUTING.md)**

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **[quickstart-first-presentation.md](docs/quickstart-first-presentation.md)** | Step-by-step: create your first deck (5 min) |
| **[architecture-overview.md](docs/architecture-overview.md)** | Build pipeline, modules, data flow |
| **[image-generation-troubleshooting.md](docs/image-generation-troubleshooting.md)** | Debug image gen, cache, providers |
| **[theme-section-10-guide.md](docs/theme-section-10-guide.md)** | Create custom themes (Visual Style Preference) |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | How to contribute, git workflow, hapai rules |
| **[CLAUDE.md](CLAUDE.md)** | Architecture for AI code assistants |

### Design Documents

```
specs/main/
├── plan.md              — M0–M4 roadmap
├── research.md          — Tech decisions
├── data-model.md        — Core entities
├── quickstart.md        — Dev recipes
└── contracts/cli-contract.md — Full CLI specs
```

---

## 🎯 Project Status

| Milestone | Status | Features |
|-----------|--------|----------|
| **M0** | ✅ Complete | CLI, parser, config, logging |
| **M1** | ✅ Complete | 8 layouts, themes, build, serve |
| **M2** | ✅ Complete | Charts, icons, extract, 57 themes |
| **M2.5** | 🚀 In Progress | SVG composites, AI image gen, 8 agents |
| **M3** | 📋 Planned | Coverage gates, perf hardening |
| **M4** | 📋 Planned | 4 distribution modes, 64+ themes |

---

## ❓ FAQ

**Q: Can I use AIO offline?**  
A: Yes! Output is a single `.html` file with zero external dependencies. Works anywhere.

**Q: How much does image generation cost?**  
A: Free by default (Pollinations). Optional paid providers: DALL-E (~$0.08/image), Unsplash (free tier, 50 req/hr).

**Q: Can I use my own theme?**  
A: Yes. Either pick from 57 built-in themes or create a custom DESIGN.md. See [theme-section-10-guide.md](docs/theme-section-10-guide.md).

**Q: What if my presentation doesn't fit the layout I want?**  
A: AIO has 8 layouts that auto-infer. If you need custom layout, you can edit the Jinja2 templates in `src/aio/layouts/`.

**Q: How fast is it?**  
A: 30-slide deck builds in < 5 seconds (without images). With image generation: ~30s first build, ~2s cached rebuilds.

👉 **[More FAQs →](docs/faq.md)**
