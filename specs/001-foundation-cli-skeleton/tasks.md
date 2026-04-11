# Tasks: AIO Foundation & CLI Skeleton (M0)

**Input**: Design documents from `specs/001-foundation-cli-skeleton/`
**Prerequisites**: plan.md ✓, spec.md ✓, data-model.md ✓, contracts/internal-api.md ✓, research.md ✓

**Tests**: Included — TDD is mandatory per Constitution Art. IX. Write each test group FIRST, verify it FAILS, then implement.

**Organization**: Tasks grouped by user story (US1–US7). Each story is independently implementable and testable.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[US#]**: User story this task belongs to
- No label = Setup / Foundational / Polish phase

---

## Phase 1: Setup

**Purpose**: Project scaffolding — package structure, tooling config, CI workflow.

- [x] T001 Create `pyproject.toml` with `[project]` metadata, `[project.dependencies]` (9 core deps), `[project.optional-dependencies]` (`dev` = pytest/mypy/ruff/pyinstaller; `enrich` = pillow/bs4/lxml/cssutils; `commands` = `pyperclip`), `[project.scripts]` entry point `aio = "aio.cli:app"`, and `[tool.setuptools.package-data]` for `*.j2`, `*.md`, `*.json`, `*.css` under `src/aio/`
- [x] T002 Create `src/aio/__init__.py` — set `__version__ = "0.1.0"` only; no other imports
- [x] T003 Create `src/aio/__main__.py` — `from aio.cli import app; app()` as entry point for `python -m aio`
- [x] T004 Create `tests/conftest.py` — fixtures: `tmp_project_dir` (tmp_path with `.aio/` scaffold), `minimal_config_yaml` (bytes), `sample_slides_md` (3-slide markdown string)
- [ ] T005 [P] Create `.github/workflows/1-lint-test.yml` — jobs: `lint` (ruff check + ruff format --check), `typecheck` (mypy src/aio/), `test` (pytest --cov=src/aio --cov-fail-under=20); trigger on pull_request and push to main; jobs run sequentially via `needs:`
- [x] T006 [P] Add `[tool.ruff]` to `pyproject.toml` — `line-length = 100`, `select = ["E", "F", "I", "UP"]`, `ignore = []`; add `[tool.ruff.format]`
- [x] T007 [P] Add `[tool.mypy]` to `pyproject.toml` — `python_version = "3.12"`, `strict = true`, `ignore_missing_imports = true`
- [x] T008 [P] Add `[tool.pytest.ini_options]` to `pyproject.toml` — `testpaths = ["tests"]`, `asyncio_mode = "auto"`, `addopts = "--tb=short"`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure modules that every user story depends on. No story work begins until this phase is complete.

**⚠️ CRITICAL**: All subsequent phases require this phase to be complete.

- [x] T009 Create `src/aio/exceptions.py` — `AIOError(Exception)` base; subclasses: `ConfigError`, `LayoutNotFoundError(name: str, suggestion: str | None)`, `ThemeNotFoundError`, `ParseError(line: int | None)`, `AgentError`
- [x] T010 Create `src/aio/_log.py` — `setup_logging(level: int = logging.INFO) -> None` (idempotent: checks handler count before adding); `get_logger(name: str) -> logging.Logger`; handler writes to `sys.stderr` only; format: `"%(levelname)s [%(name)s] %(message)s"`; root logger name `"aio"`
- [x] T011 [P] Create `src/aio/_utils.py` — `slugify(text: str) -> str` (lowercase, hyphens); `safe_id(text: str) -> str` (CSS-safe); `escape_html(text: str) -> str` (& < > " '); `_find_aio_dir(start: Path) -> Path` (walk parents to find `.aio/`; raise `AIOError` if not found or nested ambiguity)
- [x] T012 [P] Create `src/aio/_validators.py` — `yaml_safe_load(content: str, source: str = "") -> dict` (wraps `yaml.safe_load`, re-raises with source info); `validate_json_schema(data: dict, schema: dict) -> list[str]` (returns error list)
- [x] T013 Create `src/aio/themes/minimal/` — `meta.json` (ThemeRegistryEntry fields), `DESIGN.md` (11-section skeleton with placeholder content per section), `theme.css` (CSS custom properties skeleton), `layout.css` (grid skeleton), `fonts/` (empty dir with `.gitkeep`)
- [x] T014 [P] Create `src/aio/themes/modern/` — same structure as minimal; different color palette and typography in DESIGN.md
- [x] T015 [P] Create `src/aio/themes/vibrant/` — same structure as minimal; vibrant palette, bold typography
- [x] T016 Create `src/aio/themes/registry.json` — array of 3 `ThemeRegistryEntry` objects (minimal, modern, vibrant) with all fields: `id`, `name`, `description`, `tags`, `author`, `source: "builtin"`, `path`, `created_at`, `updated_at`
- [x] T017 Create `src/aio/themes/__init__.py` (empty) and `src/aio/themes/loader.py` — `resolve_theme_path(theme_id: str) -> Path` using `importlib.resources.files("aio.themes")`; `load_registry() -> list[dict]` reads global `registry.json`
- [x] T018 Create `src/aio/themes/validator.py` — `validate_theme(theme_id: str) -> list[str]` checks DESIGN.md has all 11 section headers; raises `ThemeNotFoundError` if not in registry

**Checkpoint**: `pip install -e ".[dev]"` succeeds; `python -m aio --help` runs (may error — CLI not wired yet); all theme files accessible via `importlib.resources`.

---

## Phase 3: User Story 1 — Scaffolding & Project Init (Priority: P1) 🎯 MVP

**Goal**: `aio init my-project --agent claude --theme minimal` creates a complete, ready-to-use project structure in under 1 second with zero network calls.

**Independent Test**: `aio init test-project --agent claude --theme minimal && ls test-project/.aio/ test-project/slides.md test-project/assets/ test-project/build/`

### Tests — US1 (write first, verify FAIL)

- [x] T019 [P] [US1] Write `tests/unit/test_config.py` — tests for `ProjectConfig`: load all fields from YAML, defaults applied (`"default"` → `"minimal"` alias), `ValueError` on invalid agent, `FrozenInstanceError` on mutation, all 8 agents accepted; timing assertion `elapsed < 0.010` using `time.perf_counter()` (SC-106); use `tmp_path` fixture; no mocks
- [x] T020 [P] [US1] Write `tests/unit/test_init.py` — tests for `aio init`: creates all 8 expected paths, `config.yaml` is valid YAML, invalid agent → exit 1 + no files created, `.aio/` exists without `--force` → exit 1, `--dry-run` creates no files, `--force` overwrites; use `CliRunner` from Typer
- [x] T021 [US1] Write `tests/integration/test_init_pipeline.py` — end-to-end: invoke `aio init` via subprocess in `tmp_path`, assert all paths exist, assert `config.yaml` parseable, assert `meta.json` has ISO `created_at`, assert `.aio/themes/registry.json` is < 5 KB and contains only 1 theme; assert `elapsed < 1.0` via `time.perf_counter()` around the subprocess call (SC-100)

### Implementation — US1

- [x] T022 [US1] Implement `ProjectConfig` `@dataclass(frozen=True)` in `src/aio/commands/init.py` — fields: `agent: str`, `theme: str = "default"`, `enrich: bool = False`, `serve_port: int = 8000`, `output_dir: str = "build"`; `SUPPORTED_AGENTS = frozenset({...8 agents...})`; `__post_init__`: alias `"default"` → `"minimal"`, validate agent membership, normalize `output_dir` to relative
- [x] T023 [US1] Implement `ProjectConfig.load(dir_path: str | Path) -> ProjectConfig` in `src/aio/commands/init.py` — reads `{dir_path}/config.yaml` via `yaml_safe_load()`, applies defaults, raises `ConfigError` with agent list on invalid agent
- [x] T024 [US1] Implement `ProjectConfig.to_dict() -> dict[str, Any]` in `src/aio/commands/init.py` — returns plain dict of all fields (post-alias)
- [x] T025 [US1] Define `SLIDES_MD_TEMPLATE` string constant in `src/aio/commands/init.py` — contains YAML frontmatter block (`title`, `agent`, `theme`) + 2 scaffold slides with `<!-- @layout: hero-title -->` and `<!-- @layout: content -->` annotations
- [x] T026 [US1] Implement `_create_project_structure(name: str, path: Path, config: ProjectConfig, dry_run: bool) -> None` in `src/aio/commands/init.py` — creates `.aio/`, `assets/`, `build/`; writes `config.yaml`, `meta.json` (with ISO `created_at`), per-project `themes/registry.json` (single theme subset), `slides.md` from template; if `dry_run=True` logs planned structure to stderr only
- [x] T027 [US1] Implement `init()` Typer command in `src/aio/commands/init.py` — `NAME: str = typer.Argument(None)` defaults to cwd name; `--theme`, `--agent`, `--force`, `--dry-run` options; checks `.aio/` existence; calls `_create_project_structure`; stdout: absolute path of created dir; stderr: INFO logs; exit codes 0/1
- [x] T028 [US1] Run `pytest tests/unit/test_config.py tests/unit/test_init.py tests/integration/test_init_pipeline.py -v` — all must pass

---

## Phase 4: User Story 2 — CLI Skeleton & Subcommand Routing (Priority: P1)

**Goal**: `aio --help` shows 6 subcommands with descriptions; `aio --version` prints `aio 0.1.0`; all in under 100ms.

**Independent Test**: `aio --help` (check for 6 subcommands); `aio build --help` (check for 8+ flags); `aio theme --help` (check for list/validate/search/info/use/show/create)

### Tests — US2 (write first, verify FAIL)

- [x] T029 [P] [US2] Write `tests/unit/test_cli.py` — tests: `--help` shows exactly 6 subcommands, `--version` prints `aio 0.1.0` to stdout exit 0, `--verbose` flag wires DEBUG logging, `--quiet` flag wires ERROR logging, `--quiet --verbose` together → ERROR level wins; use `CliRunner`

### Implementation — US2

- [x] T030 [US2] Create `src/aio/cli.py` — `app = typer.Typer(name="aio", help="AIO — AI-native presentation generator")`; global `@app.callback()` with `--verbose: bool`, `--quiet: bool`, `--version: bool`; version callback uses `importlib.metadata.version("aio")` → stdout; verbose/quiet → call `setup_logging()`; **NO** `from __future__ import annotations`
- [x] T031 [US2] Register all 6 subcommands in `src/aio/cli.py` — `app.add_typer(theme_app)` and `app.command()` for init, build, serve, extract, commands; each import from its commands module
- [x] T032 [P] [US2] Create `src/aio/commands/build.py` stub — `@app.command()` with `INPUT: Path` arg, `--output/-o`, `--theme`, `--enrich`, `--provider`, `--skip-existing` options; logs "not yet implemented"; exit 0; **stub only — pipeline impl is M1**
- [x] T033 [P] [US2] Create `src/aio/commands/serve.py` stub — `@app.command()` with `INPUT: Path`, `--port`, `--host`, `--no-reload`; logs stub; exit 0; **NO** `from __future__ import annotations`; create `src/aio/commands/extract.py` stub similarly
- [x] T034 [US2] Implement `--verbose`/`--quiet` precedence in `cli.py` callback — `if quiet: setup_logging(logging.ERROR)` checked before `elif verbose: setup_logging(logging.DEBUG)` else `setup_logging(logging.INFO)`
- [x] T035 [US2] Run `pytest tests/unit/test_cli.py -v` — all must pass; also manually verify `aio --help` renders in < 100ms via `time aio --help`

---

## Phase 5: User Story 3 — Layout Template Engine (Priority: P2)

**Goal**: Place a `.j2` file in `src/aio/layouts/` and it is auto-discovered, registered, and renderable via `CompositionEngine` without manual registration.

**Independent Test**: `python -c "from aio.composition.engine import CompositionEngine; e = CompositionEngine(); assert len(e.layout_registry) == 16; print('OK')"`

### Tests — US3 (write first, verify FAIL)

- [x] T037 [P] [US3] Write `tests/unit/test_layout_engine.py` — tests: all 16 layouts auto-discovered (registry length), unknown layout raises `LayoutNotFoundError` with non-None `suggestion`, `render("hero-title", {"title":"T","subtitle":"S"})` contains both values, same inputs render byte-identical, 0-block and 10-block templates load without error, a child layout that uses `{% extends "content.j2" %}` overrides one block correctly (FR-120 inheritance); use real `.j2` files via `importlib.resources`

### Implementation — US3

- [x] T038 [P] [US3] Create `src/aio/layouts/hero-title.j2` — `<section>{% block title %}Title{% endblock %} {% block subtitle %}Subtitle{% endblock %}</section>`
- [x] T039 [P] [US3] Create `src/aio/layouts/content.j2` — `{% block title %}{% endblock %}` + `{% block body %}{% endblock %}`
- [x] T040 [P] [US3] Create `src/aio/layouts/two-column.j2`, `three-column.j2`, `full-image.j2` — each with 2–3 named `{% block %}` slots relevant to the layout name
- [x] T041 [P] [US3] Create `src/aio/layouts/code.j2`, `quote.j2`, `timeline.j2` — code.j2 has `{% block code %}` + `{% block language %}`; quote.j2 has `{% block quote %}` + `{% block attribution %}`
- [x] T042 [P] [US3] Create `src/aio/layouts/comparison.j2`, `gallery.j2`, `data.j2`, `icon-grid.j2` — each with 2–4 named blocks
- [x] T043 [P] [US3] Create `src/aio/layouts/narrative.j2`, `diagram.j2`, `custom.j2`, `interactive.j2` — stubs with `{% block content %}{% endblock %}` (0–1 blocks each)
- [x] T044 [US3] Create `src/aio/layouts/__init__.py` — `LayoutRecord @dataclass(frozen=True)` with `name: str`, `path: str`, `blocks: list[str]`; `_discover_layouts() -> dict[str, LayoutRecord]` using `importlib.resources.files("aio.layouts").iterdir()`, filters `*.j2`, reads content, extracts blocks via `re.findall(r'\{%-?\s*block\s+(\w+)\s*-?%\}', content)`; `LAYOUT_REGISTRY = _discover_layouts()` at module level
- [x] T045 [US3] Create `src/aio/_tpl.py` — `make_jinja_env() -> jinja2.Environment` using `jinja2.PackageLoader("aio", "layouts")` (works in all dist modes); register filters: `markdown` (mistune render), `safe_id` (from `_utils`), `truncate` (built-in), `to_css_var` (prefix `--` + slugify)
- [x] T046 [US3] Create `src/aio/composition/__init__.py` (empty) and `src/aio/composition/engine.py` — `CompositionEngine` class: `__init__` loads `LAYOUT_REGISTRY`; `infer_layout(slide) -> str` returns `slide.metadata.get("layout", "content")`; `render(slide, layout_name, context) -> str` raises `LayoutNotFoundError(name, suggestion=difflib.get_close_matches(..., n=1))` if unknown, else renders via Jinja2 env
- [x] T047 [US3] Run `pytest tests/unit/test_layout_engine.py -v` — all must pass

---

## Phase 6: User Story 4 — Slide Parser (Priority: P2)

**Goal**: `parse_slides("slides.md")` returns a list of `SlideAST` objects with correct frontmatter, metadata dicts, and body tokens; 100 slides parse in under 50ms.

**Independent Test**: `python -c "from aio.commands.build import parse_slides; s = parse_slides('examples/quick-start-5-slides.md'); print(len(s), s[0].metadata)"`

### Tests — US4 (write first, verify FAIL)

- [x] T048 [P] [US4] Write `tests/unit/test_slide_parser.py` — tests: 3-slide file returns 3 `SlideAST` objects with correct index/frontmatter/metadata/content; `@icon`, `@color`, `@data` tags extracted correctly; `<!-- @: invalid -->` silently ignored with WARNING; `@layout: nonexistent` stored without error (WARNING); invalid YAML raises `ParseError`; 100 slides (generated fixture) parse in < 50ms via `time.perf_counter`

### Implementation — US4

- [x] T049 [US4] Define `SlideAST @dataclass` in `src/aio/commands/build.py` — `index: int`, `frontmatter: dict[str, Any]`, `title: str | None`, `body_tokens: list[Any]`, `metadata: dict[str, str]`, `raw_markdown: str`
- [x] T050 [US4] Define `DeckFrontmatter @dataclass` in `src/aio/commands/build.py` — `title: str = "Untitled"`, `author: str | None = None`, `theme: str = "default"`, `agent: str = "claude"`
- [x] T051 [US4] Implement `_split_slides(content: str) -> tuple[dict, list[str]]` in `src/aio/commands/build.py` — splits on `"\n---\n"`, extracts frontmatter from `block[0]` via `yaml_safe_load()`, raises `ParseError` with line hint on YAML error; returns `(frontmatter_dict, body_blocks)`
- [x] T052 [US4] Implement `_extract_metadata(block: str) -> tuple[dict[str, str], str]` in `src/aio/commands/build.py` — `re.finditer(r'<!--\s*@(\w+):\s*(.*?)\s*-->', block)`; skip matches where group(1) is empty (log WARNING); return `(metadata, cleaned_block)` with tags stripped
- [x] T053 [US4] Implement `parse_slides(path: str | Path) -> list[SlideAST]` in `src/aio/commands/build.py` — reads file, calls `_split_slides`, iterates blocks calling `_extract_metadata`, extracts `title` from first `# ` heading, tokenizes body via `mistune.create_markdown(renderer=None)(body)`, constructs `SlideAST` per slide
- [x] T054 [US4] Run `pytest tests/unit/test_slide_parser.py -v` — all must pass

---

## Phase 7: User Story 5 — Project Config System (Priority: P2)

**Goal**: Every CLI command auto-loads `ProjectConfig` from the nearest `.aio/` ancestor; CLI flags override config values; clear error if `.aio/` not found.

**Independent Test**: `cd /tmp && aio build slides.md` → error "No .aio/ directory found"; `cd my-project && aio build slides.md` → uses config from `.aio/config.yaml`

### Tests — US5 (write first, verify FAIL)

- [x] T055 [P] [US5] Extend `tests/unit/test_config.py` with US5 scenarios — auto-load finds nearest `.aio/`, CLI `--theme` flag overrides config theme, missing `.aio/` in build/serve raises `AIOError`, config loaded < 10ms, all 8 agents pass validation; still use real tmp dirs

### Implementation — US5

- [x] T056 [US5] Add `_find_aio_dir(start: Path) -> Path` to `src/aio/_utils.py` — walk `start.parents` up to filesystem root; return first `.aio/` found; raise `AIOError("No .aio/ directory found")` if none; raise `AIOError("Nested .aio/ ambiguity")` if multiple at same depth
- [x] T057 [US5] Update `build()`, `serve()`, `theme()` commands to call `ProjectConfig.load(_find_aio_dir(Path.cwd()))` at command entry; catch `AIOError` → stderr + exit 1
- [x] T058 [US5] Add flag-over-config resolution in `build()` and `serve()`: if `--theme` passed, override `config.theme`; if `--agent` passed, override `config.agent`; apply after `ProjectConfig.load()`
- [x] T059 [US5] Run `pytest tests/unit/test_config.py -v` — all US5 scenarios must pass

---

## Phase 8: User Story 6 — Logging & Verbose Output (Priority: P3)

**Goal**: `aio build --verbose` shows 50+ DEBUG lines on stderr; stdout stays clean; `AIO_LOG_LEVEL=DEBUG` works without the flag.

**Independent Test**: `aio theme list --verbose 2>&1 | grep '^DEBUG' | wc -l` ≥ 3; `aio theme list 2>&1 | grep '^DEBUG' | wc -l` = 0

### Tests — US6 (write first, verify FAIL)

- [x] T060 [P] [US6] Write `tests/unit/test_logging.py` — tests: default run → no DEBUG lines in captured stderr, `--verbose` → ≥ 3 DEBUG lines, `AIO_LOG_LEVEL=DEBUG` env var → DEBUG lines without flag, sensitive path segment masked in log output, any command completion → ≥ 1 stderr line; use `capfd` and `monkeypatch`

### Implementation — US6

- [x] T061 [US6] Finalize `src/aio/_log.py` — ensure `setup_logging()` is idempotent (check `logging.getLogger("aio").handlers`); add `_mask_sensitive(msg: str) -> str` — redacts sequences matching `[0-9a-f]{32,}` (API key pattern) and `Bearer\s+\S+` with `***`
- [x] T062 [US6] Add `AIO_LOG_LEVEL` env var support to `setup_logging()` — `level = os.environ.get("AIO_LOG_LEVEL", "").upper()`; map to `logging.*` constant if valid; CLI flag takes precedence over env var
- [x] T063 [US6] Add completion log line to each command handler (`_log.info("Command complete")` or similar) so ≥ 1 stderr line is guaranteed even on minimal runs
- [x] T064 [US6] Add module-level `_log = get_logger(__name__)` in every `src/aio/commands/*.py` and `src/aio/composition/engine.py`; add DEBUG log at each major step (config load, file read, etc.)
- [x] T065 [US6] Run `pytest tests/unit/test_logging.py -v` — all must pass

---

## Phase 9: User Story 7 — Agent Command Templates (Priority: P3)

**Goal**: `aio commands outline --agent claude` returns a Claude-formatted prompt offline; `aio commands list` shows all 7 commands; 8 agents produce distinct non-empty outputs.

**Independent Test**: `aio commands list` (7 lines); `aio commands outline --agent claude` (non-empty, has SYSTEM section); `aio commands outline --agent gemini` (non-empty, no SYSTEM section)

### Tests — US7 (write first, verify FAIL)

- [x] T066 [P] [US7] Write `tests/unit/test_agent_commands.py` — tests: `list_commands()` returns 7 tuples, `load_agent_template("claude", "outline")` has `has_system_prompt=True`, `load_agent_template("gemini", "outline")` has `has_system_prompt=False`, all 8 agents return non-empty `content` for all 7 commands, `len(content) < 2000` for `outline` command (SC-108), no network call made (assert no socket usage via monkeypatch)
- [x] T067 [P] [US7] Write `tests/integration/test_commands_pipeline.py` — invoke `aio commands list` via `CliRunner`, assert 7 command names in output; invoke `aio commands outline --agent claude`, assert non-empty output; invoke for all 8 agents, assert outputs differ

### Implementation — US7

- [x] T068 [P] [US7] Create `src/aio/agent_commands/claude/v1/SYSTEM.md` — Claude system prompt: role as presentation architect, DESIGN.md-aware, output format instructions
- [x] T069 [P] [US7] Create `src/aio/agent_commands/claude/v1/` remaining phases — `INIT_PHASE.md` (brief collection), `COMPOSITION_PHASE.md` (layout selection), `ENRICH_PHASE.md` (image/SVG), `REFINEMENT_PHASE.md` (transitions, polish)
- [x] T070 [P] [US7] Create `src/aio/agent_commands/{gemini,copilot,windsurf}/v1/` — same 5 files per agent; Gemini omits system role convention; Copilot matches VS Chat format
- [x] T071 [P] [US7] Create `src/aio/agent_commands/{devin,chatgpt,cursor,generic}/v1/` — Devin uses JSON input format; ChatGPT uses optional system; generic omits all agent-specific syntax
- [x] T072 [P] [US7] Create 7 generic command templates in `src/aio/agent_commands/` root — `outline.md`, `generate.md`, `refine.md`, `visual.md`, `theme.md`, `extract.md`, `build.md`; each uses `{topic}`, `{slides_count}`, `{theme}`, `{agent}` placeholders and has a one-line description comment at top
- [x] T073 [US7] Create `src/aio/agents/prompts.py` — `AgentCommandTemplate @dataclass`; `SUPPORTED_COMMANDS` dict (name → description); `load_agent_template(agent, command, version="v1") -> AgentCommandTemplate` using `importlib.resources.files("aio.agent_commands")`; raises `ValueError` for unknown agent/command, `FileNotFoundError` for missing file
- [x] T074 [US7] Add `list_agents() -> list[str]` and `list_commands() -> list[tuple[str, str]]` to `src/aio/agents/prompts.py`
- [x] T075 [US7] Add `FORMAT_CONVERTERS: dict[str, Callable[[str, str], str]]` to `src/aio/agents/prompts.py` — 8 converter functions; Claude/Copilot prepend `SYSTEM:\n{system_content}\n\nUSER:\n`; Gemini/Windsurf/Devin/Cursor/Generic use user content only; `load_agent_template` applies converter before returning
- [x] T076 [US7] Create `src/aio/commands/commands.py` — `commands_app = typer.Typer(name="commands")`; `list_cmd()` subcommand prints 7 command names + descriptions to stdout; 7 per-command subcommands (`outline`, `generate`, etc.) each accept `--agent: str` (default "claude") and `--copy: bool`
- [x] T077 [US7] Implement `--copy` in each command subcommand in `src/aio/commands/commands.py` — try `import pyperclip; pyperclip.copy(content)`, log `"Prompt copied to clipboard."` to stderr; except `Exception` → print content to stdout; always exits 0
- [x] T078 [US7] Register `commands_app` in `src/aio/cli.py` via `app.add_typer(commands_app, name="commands")`
- [x] T079 [US7] Run `pytest tests/unit/test_agent_commands.py tests/integration/test_commands_pipeline.py -v` — all must pass

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Wire remaining theme commands, verify distribution readiness, confirm Go/No-Go criteria.

- [x] T080 [P] Implement `aio theme list` in `src/aio/commands/theme.py` — load `registry.json` via `load_registry()`, render Rich `Table` with columns `ID | Name | Tags | Source`; stdout is the table; exit 0
- [x] T081 [P] Implement `aio theme validate` in `src/aio/commands/theme.py` — call `validate_theme(theme_id)`; stderr: `"✓ Theme '{id}' is valid"` or error list; exit 0/1
- [x] T082 Wire `theme_app` Typer group in `src/aio/commands/theme.py` — subcommands: `list`, `validate` (fully implemented); `search`, `info`, `use`, `show`, `create` (stubs: log "not yet implemented", exit 0 per FR-113)
- [x] T083 Verify `pyproject.toml` `[tool.setuptools.package-data]` includes `"aio": ["layouts/*.j2", "themes/**/*", "agent_commands/**/*.md", "themes/registry.json"]` — test by running `python -c "import importlib.resources; list(importlib.resources.files('aio.layouts').iterdir())"` and confirming 16 entries
- [x] T084 Run full suite: `pytest --cov=src/aio --cov-report=term-missing --cov-fail-under=20` — fix any failures; coverage must be ≥ 20%
- [x] T085 Go/No-Go validation — manually verify each criterion from `plan.md`: `pip install -e ".[dev]"` ✓, `aio --help` shows 6 subcommands in < 100ms ✓, `aio init test-project` creates all expected paths ✓, `aio commands list` shows 7 templates without network ✓, `ruff check` 0 errors ✓, `mypy` 0 errors ✓, GitHub Actions green on push ✓
- [x] T086 [P] Create `examples/quick-start-5-slides.md` — 5-slide Markdown file using YAML frontmatter (`title: Quick Start`, `agent: claude`, `theme: minimal`) and covering the 3 core layouts: hero-title, content (2×), two-column, quote; used as the integration test fixture in `quickstart.md` and by `test_slide_parser.py`

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)       → no dependencies
Phase 2 (Foundational) → Phase 1 complete
Phase 3 (US1)         → Phase 2 complete
Phase 4 (US2)         → Phase 2 complete; imports init from Phase 3
Phase 5 (US3)         → Phase 2 complete
Phase 6 (US4)         → Phase 2 complete
Phase 7 (US5)         → Phase 3 (ProjectConfig), Phase 6 (parser), Phase 4 (CLI stubs)
Phase 8 (US6)         → Phase 2 (_log.py complete), Phase 4 (CLI wired)
Phase 9 (US7)         → Phase 2 complete
Phase 10 (Polish)     → All phases complete
```

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no story dependencies
- **US2 (P1)**: Can start after Phase 2 — imports init command from US1; can overlap if init is a stub first
- **US3 (P2)**: Can start after Phase 2 — fully independent
- **US4 (P2)**: Can start after Phase 2 — fully independent
- **US5 (P2)**: Depends on US1 (ProjectConfig) and US4 (parser wired to build)
- **US6 (P3)**: Depends on US2 (CLI wired) and Phase 2 (_log.py)
- **US7 (P3)**: Can start after Phase 2 — fully independent of US1–US6

### Within Each Story

- Test file → confirm FAIL → implementation → confirm PASS
- Dataclasses and utilities before command logic
- Each story complete and tested before Polish phase

---

## Parallel Execution Examples

### Phase 2 — All foundational tasks can run in parallel:

```
Task T009: exceptions.py
Task T010: _log.py
Task T011: _utils.py       ← [P]
Task T012: _validators.py  ← [P]
Task T013: themes/minimal/ 
Task T014: themes/modern/  ← [P]
Task T015: themes/vibrant/ ← [P]
```

### Phase 5 — Layout templates fully parallelizable:

```
Task T038: hero-title.j2   ← [P]
Task T039: content.j2      ← [P]
Task T040: two-column, three-column, full-image ← [P]
Task T041: code, quote, timeline               ← [P]
Task T042: comparison, gallery, data, icon-grid ← [P]
Task T043: narrative, diagram, custom, interactive ← [P]
```

### Phase 9 — Agent directories fully parallelizable:

```
Task T068: claude/v1/SYSTEM.md                      ← [P]
Task T069: claude/v1/ remaining phases (INIT, COMPOSITION, ENRICH, REFINEMENT) ← [P]
Task T070: gemini, copilot, windsurf /v1/            ← [P]
Task T071: devin, chatgpt, cursor, generic /v1/      ← [P]
Task T072: 7 generic command templates (outline.md … build.md) ← [P]
```

---

## Implementation Strategy

### MVP: US1 + US2 only (stops at Phase 4 Checkpoint)

1. Complete Phase 1 + Phase 2
2. Complete Phase 3 (US1: `aio init` works end-to-end)
3. Complete Phase 4 (US2: `aio --help` shows 6 subcommands, `--version` works)
4. **STOP and validate**: `aio init my-deck && aio --help && aio --version`
5. All Go/No-Go criteria for US1/US2 pass → M0 is demoable

### Full M0

Add phases 5–10 in priority order (US3 + US4 in parallel, then US5, then US6 + US7 in parallel, then Polish).

---

## Notes

- `[P]` tasks operate on different files with no shared mutable state — safe to parallelize
- TDD: each test batch must be written and confirmed FAILING before its implementation phase begins
- `from __future__ import annotations` is **forbidden** in `cli.py` and `serve.py`
- `yaml.safe_load()` **exclusively** — never `yaml.load()`
- No `print()` in any production module — use `get_logger(__name__)`
- `importlib.resources.files()` for all asset access — never `Path(__file__).parent`
- `--quiet` beats `--verbose` when both flags passed (FR-112a / FR-131)
- T036 intentionally not used (reserved gap from prior task restructuring)
- `"default"` theme auto-aliases to `"minimal"` in `ProjectConfig.__post_init__` (FR-129)
- `--force` on `aio init` overwrites existing `.aio/` without prompt (FR-109a)
- `aio theme` has 7 sub-subcommands; only `list` and `validate` are fully implemented in M0 (FR-113)
