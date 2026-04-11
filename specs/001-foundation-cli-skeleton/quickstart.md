# Quickstart: M0 Foundation & CLI Skeleton

**Phase 1 Output** | **Date**: 2026-04-11 | **Feature**: `001-foundation-cli-skeleton`

---

## Prerequisites

- Python 3.12+ (`python --version`)
- git
- Feature branch checked out: `001-foundation-cli-skeleton`

---

## Setup

```bash
# From repo root on branch 001-foundation-cli-skeleton
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"            # Installs core + dev/test deps

# Verify install
aio --help                         # Should show 6 subcommands
aio --version                      # Should print: aio 0.1.0
```

---

## Running Tests

```bash
# Unit tests only (fast — no file system I/O)
pytest tests/unit/ -v

# Integration tests (uses temp directories)
pytest tests/integration/ -v

# Full suite with coverage
pytest --cov=src/aio --cov-report=term-missing

# Single test by name
pytest -k "test_project_config_defaults" -v

# Single test file
pytest tests/unit/test_config.py -v
```

---

## CLI Verification

```bash
# Project init
aio init my-test-deck --agent claude --theme minimal
ls my-test-deck/           # slides.md  assets/  build/  .aio/
cat my-test-deck/.aio/config.yaml

# Dry run (no files created)
aio init dry-run-test --dry-run

# Error cases
aio init bad-agent --agent bad-agent   # exit 1, clear error message

# Theme commands
aio theme list                         # Shows 3 bootstrap themes
aio theme validate minimal             # Should pass

# Agent commands
aio commands list                      # Shows 7 commands
aio commands outline --agent claude    # Claude-formatted prompt
aio commands outline --agent gemini    # Gemini-formatted prompt (no system section)

# Help
aio --help
aio init --help
aio theme --help                       # Shows list, search, info, use, show, create
```

---

## Lint & Type Check

```bash
ruff check src/ tests/
ruff format src/ tests/
mypy src/aio/
```

---

## Verifying Key Behaviors

### Layout auto-discovery

```python
from aio.composition.engine import CompositionEngine
engine = CompositionEngine()
print(engine.layout_registry.keys())   # Should show 16 layout names
```

### ProjectConfig immutability

```python
from aio.commands.init import ProjectConfig
cfg = ProjectConfig.load("my-test-deck/.aio")
try:
    cfg.agent = "gemini"               # Should raise FrozenInstanceError
except Exception as e:
    print(e)
```

### Slide parser

```python
from aio.commands.build import parse_slides
slides = parse_slides("my-test-deck/slides.md")
print(len(slides))                      # Number of slides
print(slides[0].metadata)              # Per-slide @tag metadata
```

### Logging

```bash
# Default: INFO only on stderr
aio theme list 2>&1 | grep -E "^(INFO|DEBUG)"

# Verbose: DEBUG on stderr
aio theme list --verbose 2>&1 | grep "^DEBUG" | wc -l   # Should be >= 3

# Env var override
AIO_LOG_LEVEL=DEBUG aio theme list 2>&1 | head -5
```

---

## Adding a New Agent Format Converter

1. Open `src/aio/agents/prompts.py`
2. Add a new function `convert_for_myagent(content: str) -> str`
3. Register it in `FORMAT_CONVERTERS: dict[str, Callable]`
4. Create `src/aio/agent_commands/myagent/v1/*.md` files
5. Add smoke test: `pytest tests/unit/test_agent_commands.py -k "myagent" -v`

---

## Adding a New Layout

1. Create `src/aio/layouts/my-layout.j2` with at least one `{% block content %}` definition
2. No registration needed — auto-discovered at import time
3. Verify: `from aio.composition.engine import CompositionEngine; print("my-layout" in CompositionEngine().layout_registry)`
4. Add unit test in `tests/unit/test_layout_engine.py`

---

## CI/CD

```bash
# Simulate CI locally
ruff check src/ tests/ && ruff format --check src/ tests/ && mypy src/aio/ && pytest --cov=src/aio --cov-fail-under=20
```

Workflow: `.github/workflows/1-lint-test.yml` — triggers on PR and push to main.
Coverage gate for M0: ≥ 20% (rises to 80% at M3).
