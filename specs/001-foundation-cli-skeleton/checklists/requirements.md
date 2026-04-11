# Requirements Checklist: AIO Foundation & CLI Skeleton (M0)

**Purpose**: Validate that the spec covers all requirements completely and unambiguously before implementation begins.
**Created**: 2026-04-11
**Feature**: [spec.md](../spec.md)

---

## Completeness

- [x] CHK001 All 7 user stories have at least 3 acceptance scenarios each (US1–US7 have 5 each ✓)
- [x] CHK002 Every functional requirement (FR-100 to FR-138 + FR-109a + FR-112a) is traceable to at least one acceptance scenario — verified in speckit.analyze pass 3 (100% FR coverage)
- [x] CHK003 All exit codes defined in CLI contract are reflected in acceptance scenarios — exit 0/1/2 covered in US1 scenario 3, US2 scenario 4, FR-114
- [x] CHK004 Stdout/stderr separation is specified for every command — FR-108, FR-130, contracts/internal-api.md stdout/stderr table
- [x] CHK005 `--dry-run` flag is covered by at least one acceptance scenario (US1 scenario 5 ✓)
- [x] CHK006 `--verbose` flag is covered across multiple user stories (US2, US6 ✓)
- [x] CHK007 All 8 supported agents are listed and validated in requirements (FR-102, FR-136 ✓)

## Ambiguity

- [x] CHK008 "under 1 second" (SC-100) — test environment defined in SC-104 footnote (i5/i7, 8 GB RAM, SSD); perf_counter measurement specified in T021
- [x] CHK009 "fuzzy match" suggestion for unknown layouts — resolved in research.md: `difflib.get_close_matches(name, registry, n=1, cutoff=0.6)`; specified in T046
- [x] CHK010 "auto-discovery" of `.j2` files — file scanning path anchored to `src/aio/layouts/` via `importlib.resources.files("aio.layouts").iterdir()` (T044) ✓
- [x] CHK011 `slides.md` scaffold content — SLIDES_MD_TEMPLATE constant defined in T025: YAML frontmatter + 2 scaffold slides with `<!-- @layout: hero-title -->` and `<!-- @layout: content -->`
- [x] CHK012 Log format — resolved in contracts/internal-api.md: `"%(levelname)s [%(name)s] %(message)s"` (no timestamp in default format; ISO 8601 available via file handler if needed)

## Testability

- [x] CHK013 Each user story has an "Independent Test" that can be run in isolation ✓
- [x] CHK014 SC-100 through SC-109 are measurable and have defined pass/fail thresholds ✓
- [x] CHK015 Timing SCs use `time.perf_counter()` in test assertions — SC-100 in T021, SC-104 in T048, SC-106 in T019; machine spec in SC-104 footnote
- [x] CHK016 US3 "byte-identical output" (scenario 5) — deterministic Jinja2 render; same inputs → same output; test uses direct string equality (T037)
- [x] CHK017 US6 "50+ debug lines" — T064 adds DEBUG log at every major step across all commands; threshold validated in T060

## Constitutional Compliance

- [x] CHK018 No `from __future__ import annotations` in `cli.py` or `serve.py` — enforced in T030, T033, T046 notes; listed in tasks.md Notes section
- [x] CHK019 All YAML parsing uses `yaml.safe_load()` — FR-126, _validators.py wrapper in T012; `yaml.load()` never called
- [x] CHK020 `stdout` reserved for pipeable output — FR-108; no `print()` in production code (tasks.md Notes); `get_logger(__name__)` used everywhere
- [x] CHK021 All 8 agents in FR-102 match Art. IV list exactly: claude, gemini, copilot, windsurf, devin, chatgpt, cursor, generic ✓
- [x] CHK022 `ProjectConfig` is frozen dataclass — FR-127, T022; mutation raises `FrozenInstanceError` (tested in T019) ✓
- [x] CHK023 Init creates `.aio/themes/registry.json` with only selected theme — FR-107, T026; per-project registry is single-theme subset ✓
- [x] CHK024 No network calls during `aio init` — FR-109, SC-100; zero network calls asserted in T021 ✓

## Edge Cases Coverage

- [x] CHK025 `.aio/` already exists → aborts without `--force`; overwrites with `--force` — US1 scenario 4, FR-109a, T020 ✓
- [x] CHK026 Invalid agent name → exit 1, clear error, no files created — US1 scenario 3, SC-102, T019/T020 ✓
- [x] CHK027 Unknown layout → `LayoutNotFoundError` with fuzzy suggestion — US3 scenario 3, FR-121, T037/T046 ✓
- [x] CHK028 Malformed `<!-- @: invalid -->` (no key) → silently ignored, WARNING logged — US4 scenario 3, FR-125, T052 ✓
- [x] CHK029 Minimal config.yaml → defaults applied (`"default"` → `"minimal"`, enrich=False, serve_port=8000) — US5 scenario 2, FR-129, T022 ✓
- [x] CHK030 `--verbose` + `--quiet` simultaneously — **RESOLVED** in clarification session 2026-04-11 (Q3): `--quiet` always wins (ERROR level); no error raised. Documented in FR-112a, FR-131, edge cases, T029/T034.
- [x] CHK031 Agent command template for `generic` agent — fallback format: user content only, no agent-specific syntax (T071, T075) ✓
- [x] CHK032 Layout with 0 blocks — valid; empty `blocks` list; loads without error (US3 scenario 4, T037, T043) ✓

## Dependencies & Risks

- [x] CHK033 Typer + Rich — confirmed compatible: typer 0.12.0 depends on rich ≥ 10.11.0; plan.md specifies rich 13.7.0; no version conflict
- [x] CHK034 `mistune 3.0+` AST token format — `body_tokens: list[Any]` in SlideAST (data-model.md); mistune 3.x renderer=None returns token list; matched in T049/T053
- [x] CHK035 `watchdog 3.0+` in core deps but not exercised in M0 — serve.py is a stub in M0 (T033); watchdog exercised in M1 hot-reload; acceptable per plan.md
- [x] CHK036 Agent command templates use `agent_commands/{agent}/v1/` structure — matches Art. XI versioned-commands requirement; T068–T072 create the exact structure ✓
- [x] CHK037 Layout auto-discovery regex handles Jinja2 whitespace variants — regex `r'\{%-?\s*block\s+(\w+)\s*-?%\}'` in T044 covers `{% block %}`, `{%- block -%}`, `{%- block %}` variants ✓

## Notes

- Check items off as completed: `[x]`
- All 37 items verified and closed: 2026-04-11 (post speckit.clarify × 3 + speckit.analyze × 3)
- CHK030 resolved: `--quiet` takes precedence over `--verbose` (FR-112a, FR-131)
