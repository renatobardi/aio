# Feature Specification: AIO Foundation & CLI Skeleton (M0)

**Feature Branch**: `001-foundation-cli-skeleton`
**Created**: 2026-04-11
**Status**: Draft
**Input**: AIO Foundation & CLI Skeleton — 7 user stories (P1–P7) covering project scaffolding, CLI routing, layout engine, slide parser, config system, logging, and agent command templates.

---

## Clarifications

### Session 2026-04-11

- Q: Is `aio commands` a 6th top-level subcommand or nested under an existing one? → A: Add as 6th top-level subcommand; update FR-100 and SC-101.
- Q: Does a `"default"` theme ID exist in the registry, or does `ProjectConfig` need to resolve it? → A: `"default"` is aliased to `"minimal"` inside `ProjectConfig.__post_init__`; no phantom theme entry in registry.
- Q: When `--verbose` and `--quiet` are both passed, which takes precedence? → A: `--quiet` always wins regardless of flag order; no error raised.
- Q: Is `--force` for `aio init` a formal flag or should the edge case be removed? → A: Add `--force` as a formal flag; overrides existing `.aio/` without prompt.
- Q: Should `aio theme validate` be listed in FR-113? → A: Yes; add `validate` to FR-113; `search`, `info`, `use`, `show`, `create` remain stubs in M0.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Scaffolding & Project Init (Priority: P1)

A first-time AIO user runs `aio init my-deck --agent claude --theme minimal` and gets a fully-structured project directory ready to use without needing to understand internals.

**Why this priority**: Project init is the entry point for every user. Nothing else works without it.

**Independent Test**: Run `aio init test-project --agent claude --theme default` and verify all 8 expected files/directories exist and are valid without running any other command.

**Acceptance Scenarios**:

1. **Given** no `.aio/` directory exists in the target location, **When** the user runs `aio init my-project`, **Then** `my-project/.aio/config.yaml`, `.aio/meta.json`, `.aio/themes/registry.json`, `slides.md`, `assets/`, and `build/` are all created; stdout confirms success; init completes in under 1 second with no network calls.

2. **Given** the user specifies `--agent claude --theme linear` and both exist in the registry, **When** init runs, **Then** `.aio/config.yaml` contains `agent: claude`, `theme: linear`, `enrich: false`, `serve_port: 8000`; `slides.md` includes `<!-- @layout: hero-title -->` scaffold comments; `.aio/themes/registry.json` contains only the selected theme's metadata.

3. **Given** the user specifies `--agent invalid-ai`, **When** init runs, **Then** no files are created, stderr shows `Unknown agent 'invalid-ai'. Supported: claude, gemini, copilot, windsurf, devin, chatgpt, cursor, generic`, and exit code is 1.

4. **Given** `.aio/` already exists in the target directory, **When** `aio init` is run without `--force`, **Then** init aborts with a clear error; no existing files are modified.

5. **Given** the user passes `--dry-run`, **When** init runs, **Then** the planned directory structure is printed to stderr but no files or directories are created.

---

### User Story 2 — CLI Skeleton & Subcommand Routing (Priority: P1)

A developer runs `aio --help` and sees 6 subcommands with clear descriptions, self-documented via type hints, without consulting external documentation.

**Why this priority**: A well-structured CLI is the foundation for all subcommands. Without it, no feature is discoverable.

**Independent Test**: Run `aio --help`, `aio build --help`, and `aio theme --help` and verify expected output without any project directory being present.

**Acceptance Scenarios**:

1. **Given** AIO is installed, **When** the user runs `aio --help`, **Then** stdout shows 6 subcommands (`init`, `build`, `serve`, `theme`, `extract`, `commands`) each with a one-line description; `--version` and `--help` options are listed; response time is under 100ms.

2. **Given** the user runs `aio build --help`, **Then** stdout shows at least 8 flags (`--input`, `--output`, `--theme`, `--enrich`, `--agent`, `--verbose`, `--dry-run`, plus at least one more) each with a short description.

3. **Given** the user runs `aio theme --help`, **Then** stdout shows sub-subcommands including `list`, `search`, `info`, `use`, `show`, `create`.

4. **Given** the user runs `aio --version`, **Then** stdout shows `aio 0.1.0` and exit code is 0.

5. **Given** the user passes `--verbose` to any subcommand, **Then** at least 3 DEBUG-level lines appear in stderr; stdout is unaffected.

---

### User Story 3 — Layout Template Engine & Jinja2 Integration (Priority: P2)

A theme developer creates a new layout `.j2` file and it is automatically discovered and usable from a slide's `<!-- @layout: my-layout -->` annotation without modifying any Python code.

**Why this priority**: The layout engine is the foundation for visual composition. All slide rendering depends on it.

**Independent Test**: Create a minimal `hero-title.j2` with two named blocks, render it with a context dict, and verify the output HTML is correct and deterministic.

**Acceptance Scenarios**:

1. **Given** `src/aio/layouts/hero-title.j2` exists with `{% block title %}` and `{% block subtitle %}` blocks, **When** the layout engine loads, **Then** the registry contains `"hero-title": { "path": "...", "blocks": ["title", "subtitle"] }` without any manual registration.

2. **Given** layout `hero-title` is loaded and context `{ "title": "Welcome", "subtitle": "To AIO" }` is passed, **When** rendered, **Then** the output HTML contains both values; blocks not in context use template defaults; render completes in under 1ms.

3. **Given** a slide references `<!-- @layout: unknown-layout -->`, **When** the build runs, **Then** build fails with exit code 1, error message names the unknown layout, and a fuzzy suggestion is offered (e.g., `Did you mean 'hero-title'?`).

4. **Given** 16 `.j2` files exist in `src/aio/layouts/`, **When** the engine starts, **Then** all 16 are in the registry; a layout with 0 blocks and one with 10+ blocks both load without error.

5. **Given** the same input is rendered twice, **Then** the output is byte-identical (deterministic).

---

### User Story 4 — Slide Parser & Markdown Metadata (Priority: P2)

A user writes `<!-- @layout: hero-title -->` and `<!-- @key: value -->` annotations in `slides.md` and the parser extracts them without corrupting the markdown content.

**Why this priority**: The parser is the entry point of the build pipeline. All downstream processing depends on accurate splitting and metadata extraction.

**Independent Test**: Parse a 3-slide `slides.md` with YAML frontmatter and per-slide `@layout` annotations; verify each slide's metadata dict and content string are correct without running the full build.

**Acceptance Scenarios**:

1. **Given** a `slides.md` with YAML frontmatter and two `---`-separated slides each with `<!-- @layout: ... -->` annotations, **When** parsed, **Then** frontmatter is returned as a dict; each slide has correct `metadata` dict and `content` string containing no comment tags; 100 slides parse in under 50ms.

2. **Given** a slide with `<!-- @icon: brain -->`, `<!-- @color: #FF5733 -->`, `<!-- @data: 2024:50, 2025:75 -->`, **When** parsed, **Then** `metadata["icon"] == "brain"`, `metadata["color"] == "#FF5733"`, `metadata["data"] == "2024:50, 2025:75"`.

3. **Given** a slide with `<!-- @: invalid -->` (no key), **When** parsed, **Then** the tag is silently ignored; a WARNING is logged; no error is raised.

4. **Given** a slide with `<!-- @layout: nonexistent -->`, **When** parsed, **Then** a WARNING is logged but the slide object is returned with `metadata["layout"] = "nonexistent"` (layout validation is the build step's responsibility).

5. **Given** invalid YAML in the frontmatter block, **When** parsed, **Then** a clear error is raised pointing to the problematic line; parsing stops.

---

### User Story 5 — Project Config System & `.aio` Directory (Priority: P2)

A developer calls `ProjectConfig.load(".aio")` and gets a typed, validated, immutable config object; all CLI commands share the same config without repetition.

**Why this priority**: A unified config system prevents duplication and inconsistency across CLI commands.

**Independent Test**: Write a minimal `.aio/config.yaml`, call `ProjectConfig.load(".aio")`, and assert all field values and defaults without invoking any CLI command.

**Acceptance Scenarios**:

1. **Given** `.aio/config.yaml` with all fields set, **When** `ProjectConfig.load(".aio")` is called, **Then** all fields (`agent`, `theme`, `enrich`, `serve_port`, `output_dir`) match the YAML values; loading completes in under 10ms.

2. **Given** `.aio/config.yaml` with only `agent: claude`, **When** loaded, **Then** `theme == "minimal"` (aliased from `"default"`), `enrich == False`, `serve_port == 8000`, `output_dir == "build"` are applied as defaults.

3. **Given** `.aio/config.yaml` with `agent: invalid`, **When** loaded, **Then** a `ValueError` is raised with message `"agent must be one of [claude, gemini, ...]. Got 'invalid'"`.

4. **Given** the config object is loaded, **When** any attribute is mutated directly, **Then** the mutation is rejected (frozen dataclass).

5. **Given** each of the 8 supported agent names is set in config and loaded, **Then** all 8 are accepted without error.

---

### User Story 6 — Logging & Verbose Output (Priority: P3)

A user runs `aio build --verbose` and sees structured DEBUG logs on stderr tracing each pipeline step, while stdout remains clean for piping.

**Why this priority**: Structured logging is essential for debugging and is used by every subcommand.

**Independent Test**: Run any CLI command with `--verbose` and verify at least 3 DEBUG lines appear on stderr only; run without `--verbose` and verify DEBUG lines are absent.

**Acceptance Scenarios**:

1. **Given** `aio build` is run without `--verbose`, **When** it completes, **Then** stderr shows fewer than 10 lines (INFO level only); stdout shows only the output file path.

2. **Given** `aio build --verbose` is run, **When** it completes, **Then** stderr shows 50+ lines including DEBUG entries for config load, slide parse, layout resolve, render, and inline steps; stdout is unchanged.

3. **Given** `AIO_LOG_LEVEL=DEBUG` is set in the environment without `--verbose`, **When** any command runs, **Then** DEBUG logs appear; the env var overrides the default.

4. **Given** a log entry would include an API key in a file path, **When** logged, **Then** the key portion is masked.

5. **Given** any command runs to completion (success or failure), **Then** at least 1 line appears on stderr.

---

### User Story 7 — Agent Command Templates (7 × 8 Formats) (Priority: P3)

A developer runs `aio commands generate --agent gemini` and gets a ready-to-paste prompt formatted specifically for Gemini, without network access.

**Why this priority**: Agent command templates are the bridge between AIO and AI agents. They are vendored at release and used by 8 integrations.

**Independent Test**: Run `aio commands list` and verify all 7 commands are discovered; run `aio commands outline --agent claude` and verify a non-empty formatted prompt is returned without network access.

**Acceptance Scenarios**:

1. **Given** `src/aio/agent_commands/` contains 7 generic template `.md` files, **When** `aio commands list` runs, **Then** stdout lists all 7 commands (`outline`, `generate`, `refine`, `visual`, `theme`, `extract`, `build`) with descriptions; no network access is made.

2. **Given** `aio commands outline --agent claude` is run, **Then** the output contains a system prompt section and a user prompt section formatted for Claude; total length is under 2000 characters.

3. **Given** `aio commands outline --agent gemini` is run, **Then** the output contains only a user prompt (no system prompt section); it differs from the Claude output; total length is under 300 tokens.

4. **Given** `aio commands outline --agent claude --copy` is run and clipboard is available, **Then** the prompt is copied and stderr confirms `"Prompt copied to clipboard."`; when clipboard is unavailable, the prompt is printed to stdout.

5. **Given** template `.md` files are edited on disk, **When** `aio commands outline --agent claude` runs again, **Then** the updated content is returned without Python recompilation.

---

### Edge Cases

- `aio init` with `.aio/` already existing → refuses without `--force`; no existing files modified.
- Registry JSON malformed → fallback to `default` theme; WARNING logged.
- Markdown `---` inside a code block → treated as content; no spurious slide split.
- 1000+ slides in one file → parser remains O(n); no timeout.
- Unicode and emoji in `@key: value` tags → preserved exactly; no sanitization applied.
- `.j2` template with Jinja2 syntax error → error surfaced at engine-load time, not at per-slide render time.
- `serve_port` already in use → descriptive error with port number; no crash.
- `--verbose` and `--quiet` passed together → `--quiet` wins (ERROR level); no error raised; a single INFO line confirming quiet mode is suppressed.
- Absolute path in `output_dir` in `.aio/config.yaml` → normalized to relative to `.aio/` parent.
- Nested `.aio/` directories → nearest parent used; ambiguity is an error.
- 8th agent (`generic`) → generic template is returned; quality may be lower than agent-specific templates.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-100:** CLI root is Typer-based with subcommands `init`, `build`, `serve`, `theme`, `extract`, `commands` (6 top-level subcommands).
- **FR-101:** `aio init [name]` creates `.aio/`, `slides.md`, `assets/`, `build/` in one atomic operation.
- **FR-102:** `--agent` accepts exactly 8 values: `claude`, `gemini`, `copilot`, `windsurf`, `devin`, `chatgpt`, `cursor`, `generic`.
- **FR-103:** `--theme` validates against the global theme registry; invalid theme → error before any file creation.
- **FR-104:** `.aio/config.yaml` stores `agent`, `theme`, `enrich` (bool), `serve_port` (int), `output_dir` (str).
- **FR-105:** `.aio/meta.json` stores `project_name`, `created_at` (ISO 8601), `version`, optional `author`.
- **FR-106:** `slides.md` scaffold includes valid YAML frontmatter and layout annotation comments.
- **FR-107:** `.aio/themes/registry.json` contains only the selected theme's metadata (not the full global registry).
- **FR-108:** Stdout is reserved for pipeable output; all progress/status goes to stderr.
- **FR-109:** `--dry-run` flag prints planned structure to stderr without creating files.
- **FR-109a:** `--force` flag on `aio init` overwrites an existing `.aio/` directory without prompting; without `--force`, init aborts with exit code 1 if `.aio/` already exists.
- **FR-110:** `aio --help` renders 6 subcommands with one-line descriptions in under 100ms.
- **FR-111:** `aio --version` prints `aio <version>` to stdout; version sourced from `importlib.metadata`.
- **FR-112:** `--verbose` global flag enables DEBUG logging across all subcommands.
- **FR-112a:** `--quiet` global flag enables ERROR-level-only logging across all subcommands; when both `--quiet` and `--verbose` are passed, `--quiet` takes precedence and no error is raised.
- **FR-113:** `theme` subcommand is a Typer group with sub-subcommands: `list`, `validate`, `search`, `info`, `use`, `show`, `create`. In M0, only `list` and `validate` are fully implemented; the remaining five are stubs that print "not yet implemented" and exit 0.
- **FR-114:** Exit codes: 0 success, 1 general error, 2 CLI/argument error.
- **FR-115:** `src/aio/layouts/` holds 16+ Jinja2 `.j2` template files used by the composition engine.
- **FR-116:** Layout registry auto-discovers all `.j2` files and extracts `{% block name %}` definitions via scan.
- **FR-117:** Jinja2 `Environment` uses `PackageLoader("aio", "layouts")` (importlib-compatible) for the layouts directory; `FileSystemLoader` MUST NOT be used as it fails in zipapp and PyInstaller distribution modes (Art. XII).
- **FR-118:** Custom Jinja2 filters: `markdown`, `safe_id`, `truncate`, `to_css_var`.
- **FR-119:** Layout engine is stateless and thread-safe.
- **FR-120:** Layout inheritance supported via Jinja2 `{% extends %}`.
- **FR-121:** Unknown layout referenced in a slide → build exits code 1 with fuzzy suggestion.
- **FR-122:** Slide parser splits on `---` separators and extracts YAML frontmatter from the first block.
- **FR-123:** Per-slide metadata extracted from `<!-- @key: value -->` HTML comments; comments stripped from rendered content.
- **FR-124:** `<!-- @layout: name -->` overrides layout inference for that slide.
- **FR-125:** Malformed `@` tags (no key) are silently ignored with a WARNING log.
- **FR-126:** Parser is O(n); no catastrophic backtracking regex permitted.
- **FR-127:** `ProjectConfig` is a frozen dataclass with fields: `agent`, `theme`, `enrich`, `serve_port`, `output_dir`.
- **FR-128:** `ProjectConfig.load(dir_path)` raises `ValueError` for invalid agent or missing required fields.
- **FR-129:** `ProjectConfig` applies defaults: `enrich=False`, `serve_port=8000`, `output_dir="build"`, `theme="default"`. The value `"default"` is aliased to `"minimal"` inside `__post_init__` before registry validation — no `"default"` entry exists in the registry.
- **FR-130:** `_log.py` provides `setup_logging(level)` writing structured messages to stderr only.
- **FR-131:** Log level controlled by `--verbose` flag or `AIO_LOG_LEVEL` environment variable. When both `--verbose` and `--quiet` are passed, `--quiet` takes precedence (ERROR level); no error is raised.
- **FR-132:** `src/aio/agent_commands/` holds 7 generic template `.md` files: outline, generate, refine, visual, theme, extract, build.
- **FR-133:** Each template uses placeholders: `{topic}`, `{slides_count}`, `{theme}`, etc.
- **FR-134:** Agent format converters transform generic templates to agent-specific formats (system prompt presence, token limits).
- **FR-135:** `aio commands list` lists all 7 commands with descriptions; no network access.
- **FR-136:** `aio commands [command] --agent [agent]` outputs the formatted prompt to stdout.
- **FR-137:** `aio commands [command] --agent [agent] --copy` copies to clipboard; falls back to stdout if clipboard unavailable.
- **FR-138:** Templates are vendored files; editable without Python recompilation; frozen per release.

### Key Entities

- **ProjectConfig**: `agent`, `theme`, `enrich`, `serve_port`, `output_dir` — frozen, validated on load from `.aio/config.yaml`.
- **SlideAST**: `index`, `frontmatter`, `title`, `body_tokens`, `metadata` dict, `raw_markdown` — produced by the parser per slide.
- **LayoutRecord**: `name`, `path`, `blocks` list — auto-discovered from `.j2` files in `src/aio/layouts/`.
- **AgentCommandTemplate**: `command`, `agent`, `content`, `has_system_prompt` — rendered from generic `.md` template via agent format converter.
- **DeckFrontmatter**: `title`, `author`, `theme`, `agent` — parsed from the first `---` block of `slides.md`; values serve as deck-level defaults overridable per slide.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-100:** `aio init test --agent claude --theme default` creates all 8 expected paths in under 1 second (measured via `time.perf_counter()` in the integration test) with zero network calls.
- **SC-101:** `aio --help` renders all 6 subcommands in under 100ms from a cold start.
- **SC-102:** An invalid agent name produces exactly 1 actionable error message, exit code 1, and no partial file creation.
- **SC-103:** `.aio/themes/registry.json` is under 5 KB for any single-theme project.
- **SC-104:** 100 slides parse in under 50ms on a standard developer machine (i5/i7 equivalent, 8 GB RAM, SSD — consistent with the project performance baseline in `specs/main/plan.md`).
- **SC-105:** All 16+ layouts are auto-discovered without manual registration; an unknown layout produces a fuzzy suggestion error.
- **SC-106:** `ProjectConfig.load()` completes in under 10ms (measured via `time.perf_counter()` in unit test); invalid agent produces a clear error.
- **SC-107:** `aio build --verbose` produces 50+ stderr debug lines; stdout contains only the output file path.
- **SC-108:** `aio commands outline --agent claude` returns a non-empty prompt under 2000 characters with zero network calls (2000 chars ≈ 500 tokens; character count is testable without external tokenizer deps).
- **SC-109:** All 7 agent commands are listable; all 8 agent names produce distinct non-empty formatted prompts.

---

## Assumptions

1. Python 3.12+ is the only supported runtime; no legacy compatibility shim needed.
2. Typer is the CLI framework; Click is the companion; `cli.py` must NOT use `from __future__ import annotations`.
3. Jinja2 is sufficient for template rendering; no heavier engine is needed for M0.
4. Target environment footprint is under 150 MB for core dependencies.
5. Reveal.js 5.x is vendored statically; vendor files must be present before M1 but are not exercised in M0.
6. CI/CD uses GitHub Actions; M0 sets up `1-lint-test.yml` with ruff, mypy, and pytest.
7. Theme registry bootstraps with 3 themes (minimal, modern, vibrant); 64+ themes come in M4.
8. All logging goes to stderr; stdout is reserved for pipeable data output only.
9. Agent command templates are vendored files — editable without Python recompilation, frozen per release tag.
10. `theme` subcommand exposes `list` and `validate` fully in M0; `search`, `info`, `use`, `show`, `create` are stubs (per FR-113).
11. `--copy` for clipboard uses `pyperclip` or equivalent; graceful fallback to stdout when clipboard is unavailable.
12. `aio commands` is an additional subcommand (6th) exposing the 7 agent prompt commands.
