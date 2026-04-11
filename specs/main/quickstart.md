# Quickstart: AIO Development

**Phase 1 Output** | **Date**: 2026-04-11

---

## Prerequisites

- Python 3.12+ (`python --version`)
- git
- (Optional for enrich/extract features) `pip install -e ".[enrich]"`

---

## Setup

```bash
# Clone and install in editable mode
git clone <repo> aio
cd aio
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"            # Installs core + dev/test deps

# Verify environment size (must be < 150 MB core)
du -sh .venv/

# Run smoke tests
pytest tests/unit/ -v
```

---

## Development Workflow

```bash
# Lint + format (runs ruff check + ruff format)
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/aio/

# Run all tests with coverage
pytest --cov=src/aio --cov-report=term-missing

# Run only unit tests (fast)
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run a single test file
pytest tests/unit/test_layout_inference.py -v

# Run a single test by name
pytest -k "test_infer_title_layout" -v
```

---

## Using the CLI During Development

```bash
# Initialize a test presentation
aio init my-test --theme minimal

# Build (produces my-test.html in current dir)
aio build my-test/slides.md -o /tmp/out.html

# Build with image enrichment (requires internet)
aio build my-test/slides.md -o /tmp/out-rich.html --enrich

# Serve with hot reload
aio serve my-test/slides.md --port 3000

# List themes
aio theme list

# Validate a theme's DESIGN.md
aio theme validate minimal

# Extract design from a website (requires internet)
aio extract https://stripe.com -o /tmp/stripe-design.md

# Show agent prompt for Claude
aio --agent claude --agent-version v1 theme info minimal
```

---

## Running the 4 Distribution Modes Locally

```bash
# Mode 1: zero-install (copy src/aio to a dir, run as module)
PYTHONPATH=/path/to/aio/src python -m aio --help

# Mode 2: zipapp
python -m zipapp src/aio -m "aio.__main__:main" -o aio.pyz
python aio.pyz --help

# Mode 3: PyInstaller binary (requires pyinstaller in dev deps)
pyinstaller build/aurea.spec
./dist/aio --help

# Mode 4: pip (already done in setup above)
aio --help
```

---

## Adding a New Layout

1. Add a new class to `src/aio/composition/layouts.py` inheriting from `BaseLayout`
2. Add a Jinja2 template: `src/aio/composition/templates/{layout_name}.html.j2`
3. Register in `CompositionEngine.LAYOUT_REGISTRY` (dict in `engine.py`)
4. Add unit tests: `tests/unit/test_layout_{name}.py`
5. Add integration test case in `tests/integration/test_full_pipeline.py`

---

## Adding a New Theme

1. Create `src/aio/themes/{theme_id}/` with: `DESIGN.md`, `theme.css`, `layout.css`, `meta.json`, `fonts/`
2. Ensure `DESIGN.md` has all 11 mandatory sections (see constitution Art. V)
3. Add entry to `src/aio/themes/registry.json`
4. Validate: `aio theme validate {theme_id}`
5. Smoke test: `aio build examples/quick-start-5-slides.md --theme {theme_id} -o /tmp/test.html`

---

## Adding a New Agent

1. Create `src/aio/agent_commands/{agent}/v1/` with 5 `.md` files:
   `SYSTEM.md`, `INIT_PHASE.md`, `COMPOSITION_PHASE.md`, `ENRICH_PHASE.md`, `REFINEMENT_PHASE.md`
2. Register in `src/aio/agents/prompts.py` → `AGENT_REGISTRY` dict
3. Add smoke test: `pytest tests/unit/test_agent_prompts.py -k "{agent}"`
4. Freeze at release (do not modify after tagging without version bump)

---

## Checking External URL Leaks (Art. II)

The build pipeline's `Pipeline.inline()` step runs this check automatically. To run manually:

```bash
# Check if an HTML file has any external URL references
python -c "
import re, sys
html = open(sys.argv[1]).read()
external = re.findall(r'(?:href|src)=[\"\'](https?://[^\"\']+)[\"\'']', html)
if external:
    print('FAIL: External URLs found:', external)
    sys.exit(3)
else:
    print('PASS: No external URLs')
" /tmp/out.html
```

---

## CI/CD Overview

| Workflow | Trigger | Jobs |
|----------|---------|------|
| `1-lint-test.yml` | PR + push main | ruff check, mypy, pytest --cov |
| `2-build-dist.yml` | Tag `vX.Y.Z` | PyInstaller (win/mac/linux), zipapp, PyPI publish |
| `3-sync-themes.yml` | Nightly cron | `scripts/import-awesome-designs.py`, validate all themes |

Coverage gate: `pytest --cov=src/aio --cov-fail-under=80` — PRs fail if < 80%.
