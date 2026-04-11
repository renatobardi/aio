# Developer Quickstart: M1 Core Layouts & Theme System

**Branch**: `002-core-layouts-theme-system`

## Prerequisites

```bash
git checkout feat/002-core-layouts-theme-system
pip install -e ".[dev]"           # installs starlette, uvicorn, watchdog, httpx
pip install -e ".[enrich]"        # needed only for image generation smoke tests
git --version                     # must be present in PATH for the import script
```

## 1. Working on Layouts

Render a single layout template in isolation without running the full build pipeline:

```bash
# Quick smoke test for one layout — outputs HTML fragment to stdout
python - <<'EOF'
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

env = Environment(loader=FileSystemLoader("src/aio/layouts"))
tmpl = env.get_template("hero_title.j2")
print(tmpl.render(title="Hello World", subtitle="M1 is live", theme_vars={}))
EOF

# Run layout unit tests only (fast, no I/O)
pytest tests/unit/test_layouts.py tests/unit/test_composition_engine.py -v
```

When adding a new layout:
1. Add the `LayoutType` enum value in `src/aio/composition/layouts.py`.
2. Create `src/aio/layouts/{name}.j2` extending `base.j2`.
3. Add an inference rule in `CompositionEngine.infer_layout()`.
4. Add a parametrized test case in `tests/unit/test_composition_engine.py`.

## 2. Working on the Theme Import Script

The import script clones `nicholasgasior/awesome-design-md` and harvests DESIGN.md files. Never run it without `--dry-run` during development — it writes to `src/aio/themes/` which is checked in.

```bash
# Dry run: see what would be imported without touching the repo
python scripts/import-awesome-designs.py --dry-run

# Import only 5 themes (for fast iteration)
python scripts/import-awesome-designs.py --limit 5 --output /tmp/theme-test/

# Validate a single theme after import
aio theme validate /tmp/theme-test/stripe-checkout/

# Test the parser against a fixture DESIGN.md
pytest tests/unit/test_theme_parser.py -v
```

If a DESIGN.md fails the 11-section check, the script logs the missing sections and skips
that theme. Run with `--verbose` to see per-file results.

## 3. Developing the Build Pipeline (5 steps)

Run the full pipeline end-to-end against the canonical fixture:

```bash
# Full build smoke test
aio build tests/fixtures/slides/sample_all_layouts.md -o /tmp/out.html
echo "Exit: $?"

# Check for external URL leaks (must print PASS)
python -c "
import re, sys
html = open(sys.argv[1]).read()
bad = re.findall(r'(?:href|src)=[\"\'](https?://[^\"\']+)[\"\'']', html)
print('FAIL:', bad) if bad else print('PASS')
" /tmp/out.html

# Run pipeline integration tests (real temp dirs, no mocks)
pytest tests/integration/test_build_e2e.py -v

# Run with timing to check the < 30s performance gate
pytest tests/integration/test_build_e2e.py -v -k "test_30_slides_performance"
```

Structured log output from each step is written to stderr. Set `AIO_LOG_LEVEL=DEBUG` to see per-step timing.

## 4. Developing Serve with Hot Reload

```bash
# Start the dev server against a fixture file
aio serve tests/fixtures/slides/sample_all_layouts.md --port 3000
# Open http://127.0.0.1:3000 in browser

# Watch server logs (SSE events are logged at DEBUG level)
AIO_LOG_LEVEL=DEBUG aio serve tests/fixtures/slides/sample_all_layouts.md --port 3000

# Run serve integration tests (uses httpx in-process transport, no real port)
pytest tests/integration/test_serve_e2e.py -v

# Test SSE endpoint directly
curl -N http://127.0.0.1:3000/__sse__
# Should stream: data: connected\n\n then data: reload\n\n on file change
```

To test the `--host` override (e.g. LAN access):

```bash
aio serve slides.md --port 3000 --host 0.0.0.0
```

## 5. Running the Full Test Suite

```bash
# All unit tests (fast, < 10s)
pytest tests/unit/ -v

# All integration tests (real I/O, ~60s)
pytest tests/integration/ -v

# Coverage check (must be >= 80% line, >= 75% branch)
pytest --cov=src/aio --cov-report=term-missing --cov-fail-under=80

# Single test by name
pytest -k "test_infer_layout_hero_title" -v
```

## 6. Common Pitfalls

**`from __future__ import annotations` in Typer files**
Never add this import to `cli.py`, `commands/serve.py`, `commands/theme.py`, or
`commands/build.py`. Typer uses `typing.get_type_hints()` at runtime; the future import
makes all annotations strings and breaks parameter inference silently. Symptom: Typer
treats every option as `str` regardless of declared type.

**External URL leaks in output HTML**
`inline_assets()` raises `ExternalURLError` (exit code 3) if any `src=`/`href=` still
points to an `http(s)://` URL after inlining. Common cause: a `.j2` template hardcoding a
CDN link. Always serve fonts and scripts from `src/aio/vendor/` or embed as base64.

**SVG `<script>` injection**
Any SVG inlined into a slide must pass through `CompositionEngine.sanitize_svg()` first.
If you add a new SVG source, add a test asserting no `<script>` tag in the output.
The sanitizer uses `xml.etree.ElementTree` — malformed XML will raise; wrap with a
try/except, log a warning, and fall back to stripping with regex.

**`yaml.safe_load()` discipline**
Never use `yaml.load()` — the import script, DESIGN.md parser, and frontmatter reader all
use `yaml.safe_load()`. A CI grep check enforces this; the pre-commit hook catches it
locally before push.

**Watchdog on macOS**
`watchdog` uses `FSEvents` on macOS (native, reliable). On Linux CI it falls back to
`inotify` — ensure the CI runner has inotify limits set high enough for tests that create
many temp files (`/proc/sys/fs/inotify/max_user_watches`).

**Layout registry requires `importlib.resources`**
Never use `__file__`-relative paths to access `.j2` templates or theme files. Use
`importlib.resources.files("aio.layouts")` so discovery works in all 4 distribution
modes (editable install, wheel, zipapp, PyInstaller).
