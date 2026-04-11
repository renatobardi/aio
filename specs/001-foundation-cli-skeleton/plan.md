# Implementation Plan: AIO Foundation & CLI Skeleton (M0)

**Branch**: `001-foundation-cli-skeleton` | **Date**: 2026-04-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification — 7 user stories (P1–P3), 39 FRs (FR-100 to FR-138), 10 SCs

## Summary

Establish the foundational Python package, Typer CLI skeleton, Jinja2 layout engine, slide parser,
project config system, structured logging, and vendored agent command templates. This milestone
produces no visual output (no Reveal.js, no HTML generation) — it is the scaffold on which all
subsequent milestones build. All 7 user stories must pass independently testable scenarios.

---

## Technical Context

**Language/Version**: Python 3.12+ (primary target; 3.10+ tolerated for extended support)
**Primary Dependencies**: typer 0.12.0, jinja2 3.1.2, mistune 3.0.2, pyyaml 6.0.1, rich 13.7.0, click 8.1.7
**Storage**: Local filesystem only — `.aio/` config dir, `~/.aio/logs/`
**Testing**: pytest 7.4.3 + pytest-cov 4.1.0 + pytest-asyncio 0.21.1; no `unittest.mock` for core pipeline
**Target Platform**: macOS, Linux, Windows (via pip and PyInstaller)
**Project Type**: CLI tool
**Performance Goals**: `aio --help` < 100ms; 100 slides parse < 50ms; `ProjectConfig.load()` < 10ms; `aio init` < 1s
**Constraints**: Core deps < 150 MB; no network calls in M0; stdout reserved for pipeable output
**Scale/Scope**: 16 layout templates, 8 agents, 7 command templates, 3 bootstrap themes

---

## Constitution Check

*GATE: All 12 articles evaluated. Re-check after Phase 1 design.*

| Article | Gate | M0 Status |
|---------|------|-----------|
| **Art. I** — Python 3.12+ | `python --version >= 3.12`; `A \| B` unions used; no `typing.Union` | ✅ PASS — spec mandates 3.12+ |
| **Art. II** — Offline HTML | No CDN refs; build fails on external URL detection | ⚠️ N/A for M0 (no HTML output yet); vendoring deferred to M1 |
| **Art. III** — Visual Intelligence | `CompositionEngine` class exists with `infer_layout()` stub | ✅ PASS — layout engine scaffold in FR-115–FR-121 |
| **Art. IV** — Agent-Agnostic | 8 agent dirs + 7 command templates vendored | ✅ PASS — FR-132 to FR-138 cover this |
| **Art. V** — DESIGN.md 11-section | 3 bootstrap themes have DESIGN.md skeleton | ⚠️ PARTIAL — full 11-section validation deferred to M1 |
| **Art. VI** — Free by Default | No paid API calls in M0 | ✅ PASS — enrichment not exercised in M0 |
| **Art. VII** — Deps < 150 MB | `pip install -e .` verified < 150 MB | ✅ PASS — 9 deps listed; no heavy additions |
| **Art. VIII** — Reveal.js 5.x | UMD vendor files not yet present | ⚠️ N/A for M0; vendor in M1 |
| **Art. IX** — 80% Coverage | `pytest --cov >= 80%` gate active from M0 | ✅ PASS — CI gate configured; 20% initial target |
| **Art. X** — 64+ Themes | 3 bootstrap themes; nightly import deferred to M4 | ⚠️ PARTIAL — acceptable at M0 |
| **Art. XI** — Versioned Agent Commands | `agent_commands/{agent}/v1/` structure created | ✅ PASS — FR-138 covers this |
| **Art. XII** — 4 Dist Modes | `pip` mode only in M0; others deferred to M4 | ⚠️ PARTIAL — acceptable at M0 |

**Gate result**: PASS with 5 partial/N/A items, all justified as deferred to later milestones. No violations.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-foundation-cli-skeleton/
├── plan.md              # This file
├── research.md          # Phase 0 — technology decisions
├── data-model.md        # Phase 1 — entity definitions
├── quickstart.md        # Phase 1 — dev setup for this feature
├── contracts/
│   └── internal-api.md  # Phase 1 — module API contracts
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/aio/
├── __init__.py                          # version = "0.1.0"
├── __main__.py                          # python -m aio entry point
├── cli.py                               # Typer root — NO from __future__ import annotations
│
├── commands/
│   ├── __init__.py
│   ├── init.py                          # aio init
│   ├── build.py                         # aio build (stub in M0)
│   ├── serve.py                         # aio serve (stub in M0) — NO from __future__
│   ├── theme.py                         # aio theme (list + validate in M0)
│   ├── extract.py                       # aio extract (stub in M0)
│   └── commands.py                      # aio commands list / outline / ...
│
├── composition/
│   ├── __init__.py
│   └── engine.py                        # CompositionEngine: infer_layout() stub, layout registry
│
├── layouts/                             # 16 Jinja2 .j2 templates
│   ├── __init__.py                      # Auto-discovery + LayoutRecord
│   ├── hero-title.j2
│   ├── content.j2
│   ├── two-column.j2
│   ├── three-column.j2
│   ├── full-image.j2
│   ├── code.j2
│   ├── quote.j2
│   ├── timeline.j2
│   ├── comparison.j2
│   ├── gallery.j2
│   ├── data.j2
│   ├── icon-grid.j2
│   ├── narrative.j2
│   ├── diagram.j2
│   ├── custom.j2
│   └── interactive.j2
│
├── agent_commands/
│   ├── claude/v1/
│   │   ├── SYSTEM.md
│   │   ├── INIT_PHASE.md
│   │   ├── COMPOSITION_PHASE.md
│   │   ├── ENRICH_PHASE.md
│   │   └── REFINEMENT_PHASE.md
│   ├── gemini/v1/   (same structure)
│   ├── copilot/v1/
│   ├── windsurf/v1/
│   ├── devin/v1/
│   ├── chatgpt/v1/
│   ├── cursor/v1/
│   └── generic/v1/
│
├── agents/
│   ├── __init__.py
│   └── prompts.py                       # load_agent_template(), list_agents()
│
├── themes/
│   ├── __init__.py
│   ├── registry.json                    # Global registry (3 bootstrap themes)
│   ├── loader.py                        # Theme path resolution
│   ├── validator.py                     # DESIGN.md schema check
│   ├── minimal/
│   │   ├── DESIGN.md
│   │   ├── theme.css
│   │   ├── layout.css
│   │   ├── meta.json
│   │   └── fonts/
│   ├── modern/   (same structure)
│   └── vibrant/  (same structure)
│
├── _log.py                              # setup_logging(level); stderr only
├── _validators.py                       # yaml.safe_load() wrapper, JSON schema
└── _utils.py                            # slugify, escape, safe_id

tests/
├── conftest.py
├── unit/
│   ├── test_cli.py                      # aio --help, --version, subcommand routing
│   ├── test_init.py                     # ProjectConfig, file creation
│   ├── test_layout_engine.py            # Auto-discovery, render, fuzzy match
│   ├── test_slide_parser.py             # Frontmatter, @tag extraction, O(n)
│   ├── test_config.py                   # ProjectConfig.load(), defaults, validation
│   ├── test_logging.py                  # setup_logging(), --verbose, AIO_LOG_LEVEL
│   └── test_agent_commands.py           # list, per-agent output, no network
└── integration/
    ├── test_init_pipeline.py            # End-to-end: aio init → file structure
    └── test_commands_pipeline.py        # End-to-end: aio commands list/outline

.github/workflows/
└── 1-lint-test.yml                      # ruff check, mypy, pytest --cov=src/aio
```

---

## Phase 0: Research

*All decisions inherited from `specs/main/research.md`. No open NEEDS CLARIFICATION.*

See [research.md](./research.md) for the consolidated decision log specific to M0 dependencies.

---

## Phase 1: Design & Contracts

### Implementation Sequence

The following order eliminates circular dependencies:

```
1. _log.py                     ← no deps on other aio modules
2. _utils.py                   ← no deps on other aio modules
3. _validators.py              ← depends on _log.py
4. ProjectConfig               ← depends on _validators.py, _log.py
5. Slide parser                ← depends on _log.py, _utils.py
6. Layout engine               ← depends on _log.py, _utils.py
7. Agent prompts               ← depends on _log.py
8. Theme loader/validator      ← depends on _log.py, _validators.py
9. CLI commands (init, theme)  ← depends on all above
10. CLI root (cli.py)          ← depends on commands
11. GitHub Actions workflow    ← depends on package being installable
```

### Key Design Decisions

**FR-116 — Layout auto-discovery**: Scan `src/aio/layouts/*.j2` at import time using
`importlib.resources` (compatible with all 4 distribution modes). Extract `{% block name %}`
via regex `r'\{%-?\s*block\s+(\w+)\s*-?%\}'`. Block extraction runs once at module load,
not per-render.

**FR-121 — Fuzzy layout suggestion**: Use `difflib.get_close_matches(name, registry.keys(), n=1, cutoff=0.6)`.
No external dependency required.

**FR-126 — O(n) parser**: Split `slides.md` on `\n---\n` using `str.split()` (not regex).
Extract `<!-- @key: value -->` tags using a single `re.finditer()` pass per slide.
No nested regex.

**FR-127 — ProjectConfig frozen dataclass**:
```python
@dataclass(frozen=True)
class ProjectConfig:
    agent: str
    theme: str = "default"
    enrich: bool = False
    serve_port: int = 8000
    output_dir: str = "build"
```

**FR-134 — Agent format converters**: Each of the 8 agents maps to a `FormatConverter`
function that takes generic template content and returns agent-specific formatted text.
Claude includes `SYSTEM:` section; Gemini omits it. Implemented as a dict of callables
in `agents/prompts.py`.

**FR-138 — Template vendoring**: `agent_commands/{agent}/v1/*.md` files are included via
`package_data` in `pyproject.toml` and accessed via `importlib.resources.files()`.
This works in all 4 distribution modes without path hacking.

---

## Complexity Tracking

No constitution violations. No complexity justification required.

---

## Go/No-Go Criteria

M0 is complete when:

- [ ] `pip install -e ".[dev]"` succeeds cleanly
- [ ] `aio --help` renders 5+ subcommands in < 100ms (6 including `commands`)
- [ ] `aio init test-project --agent claude --theme default` creates all expected paths
- [ ] `aio commands list` shows 7 templates without network access
- [ ] `pytest tests/unit/ -v` — all tests pass
- [ ] `ruff check src/ tests/` — 0 errors
- [ ] `mypy src/aio/` — 0 errors
- [ ] GitHub Actions `1-lint-test.yml` green on push
- [ ] Coverage ≥ 20% (M0 minimum; gate is 80% at M3)
