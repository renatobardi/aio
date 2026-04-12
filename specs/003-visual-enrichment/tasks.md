# Tasks: AIO Phase 2 — Visual Enrichment

**Input**: Design documents from `specs/003-visual-enrichment/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included — TDD is mandatory per Art. IX of the AIO Constitution. All test tasks MUST be written and confirmed to FAIL before the corresponding implementation task begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US5)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish test fixtures and the shared `InlineMetadata` model and parser that every user story depends on.

- [X] T001 Create test fixture `tests/fixtures/slides_phase2.md` with slides covering all Phase 2 directives (@icon, @chart, @decoration, @image-prompt)
- [X] T002 Create test fixture `tests/fixtures/mock_pollinations_response.jpg` (pre-baked JPEG bytes for deterministic enrich tests)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Inline metadata parsing (`<!-- @key: value -->`) and the extended `SlideRenderContext` are consumed by ALL five user stories. This phase MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Write unit tests in `tests/unit/test_inline_metadata.py` for `<!-- @key: value -->` extraction: correct parsing, case-insensitivity, special chars in values, multi-word values, removal from body, frontmatter-wins-on-conflict, unknown keys warned, malformed comments ignored — confirm ALL tests FAIL
- [X] T004 Add `InlineMetadata` dataclass to `src/aio/composition/metadata.py` (key: str, value: str, line: int) per data-model.md
- [X] T005 Implement `extract_inline_metadata(body: str) -> tuple[dict[str, str], str]` in `src/aio/composition/metadata.py`: regex `<!-- @([\w-]+)\s*:\s*(.*?) -->`, lowercase keys, strip tags from returned body
- [X] T006 Extend `parse_slides()` in `src/aio/commands/build.py` to call `extract_inline_metadata()` on each slide body and merge result into `SlideAST.metadata` (YAML frontmatter keys win on conflict)
- [X] T007 Extend `SlideRenderContext` in `src/aio/composition/metadata.py` with new Phase 2 fields: `icon_name`, `icon_size`, `icon_color`, `chart_svg`, `decoration_class`, `decoration_style`, `image_prompt` (all optional, per data-model.md)
- [X] T008 [P] Extend `BuildResult` in `src/aio/composition/metadata.py` with `steps_total: int = 5`
- [X] T009 Confirm T003 tests now PASS

**Checkpoint**: Inline metadata parser is functional; `SlideRenderContext` carries Phase 2 fields — user story phases can now begin.

---

## Phase 3: User Story 1 — SVG Icon Library (Priority: P1) 🎯 MVP

**Goal**: `<!-- @icon: name -->` in a slide resolves to an inline SVG; unknown icons fall back gracefully; `aio icons list` lists 200+ icons.

**Independent Test**: Build `tests/fixtures/slides_phase2.md` (which contains `<!-- @icon: sparkles -->`); verify output HTML contains `<svg class="icon icon-sparkles"` and passes the external-URL check. Run `aio icons list --count` and assert output is ≥ 200.

### Tests for User Story 1 ⚠️ Write first — confirm FAIL before implementing

- [X] T010 [P] [US1] Write unit tests in `tests/unit/test_icons.py`: `render_icon("brain")` returns valid SVG string; `render_icon("unknown")` returns fallback SVG and logs warning; `list_icons()` returns list of ≥ 200 `(name, tags)` tuples; `render_icon("brain", size="64px", color="#635BFF")` SVG contains width/height 64 and color attribute; `list_icons(filter="dataviz")` returns only icons tagged "dataviz"; individual `render_icon()` call completes in < 1 ms; `list_icons()` call completes in < 100 ms; slide with > 50 icon directives triggers advisory log — confirm ALL FAIL
- [X] T011 [P] [US1] Write integration test in `tests/integration/test_build_phase2.py`: build a single-slide deck with `<!-- @icon: brain -->` via real temp dir; assert HTML contains `icon-brain`; assert no external URLs — confirm FAILS

### Implementation for User Story 1

- [X] T012 [US1] Extend `_ICON_PATHS` in `src/aio/visuals/svg/icons.py` to reach ≥ 200 entries by adding ~41 missing Lucide v0.462 icons (cursor, diamond, divide, dumbbell, ear, egg, equal, eraser, euro, expand, eye-off, figma, film, fish, flag-off, flame, flashlight, flask-conical, flip-horizontal, flip-vertical, footprints, forklift, form-input, forward, frame, framer, frown, function-square, gamepad, gauge, gavel, gem, ghost, gift-open, git-branch-plus, git-compare, git-fork, git-merge, git-pull-request, glasses)
- [X] T013 [US1] Add `_ICON_TAGS: dict[str, list[str]]` to `src/aio/visuals/svg/icons.py` mapping each icon name to its tag list (e.g. `{"brain": ["ai", "mind", "intelligence"], "bar-chart": ["dataviz", "analytics"]}` — at minimum 1 tag per icon); then add `list_icons(filter: str | None = None) -> list[tuple[str, list[str]]]` returning sorted `(name, tags)` pairs, optionally filtered by case-insensitive tag substring
- [X] T014 [US1] Update `render_icon(name, size="48px", color=None)` in `src/aio/visuals/svg/icons.py` to accept `size` and `color` kwargs and apply them to the `<svg>` wrapper; log warning + return `help-circle` SVG for unknown names
- [X] T015 [P] [US1] Create `src/aio/commands/icons.py` with Typer subcommand `aio icons list [--filter TEXT] [--count]` that calls `list_icons(filter=...)` from `src/aio/visuals/svg/icons.py`; display output as `{name:<20} Tags: {", ".join(tags)}`; `--count` prints only the integer count
- [X] T016 [US1] Register `icons` subcommand in `src/aio/cli.py` (add `app.add_typer(icons_app, name="icons")`)
- [X] T017 [US1] Extend `compose_slides()` in `src/aio/commands/build.py` to: read `metadata.get("icon")`, call `render_icon()`, set `SlideRenderContext.icon_name` + `icon_size` + `icon_color`; wrap SVG in `<div class="icon-container">` and prepend to slide HTML; if the slide's metadata contains more than 50 icon directives, emit `_log.warning("Slide %s: 50+ icons detected — consider using fewer icons", slide_index)`
- [X] T018 [US1] Apply `CompositionEngine.sanitize_svg()` to all icon SVG output in `src/aio/commands/build.py` — no `<script>` tags allowed
- [X] T019 [US1] Confirm T010 and T011 tests now PASS

**Checkpoint**: `aio build` resolves `@icon` directives; `aio icons list` works; unknown icons fall back without halting build.

---

## Phase 4: User Story 2 — Native DataViz Engine (Priority: P2)

**Goal**: `<!-- @chart: bar -->` + `<!-- @data: ... -->` generate an inline SVG chart (bar, donut, sparkline, or timeline); existing chart types (line, pie, scatter, heatmap) continue to work.

**Independent Test**: Build a slide deck with one bar, one donut, one sparkline, and one timeline directive via real temp dir. Verify each output HTML section contains a valid `<svg>` element. Verify the bar chart SVG is byte-identical across two identical builds (determinism check). No external URLs in output.

### Tests for User Story 2 ⚠️ Write first — confirm FAIL before implementing

- [X] T020 [P] [US2] Write unit tests in `tests/unit/test_dataviz_phase2.py`: `DonutChart` renders valid SVG with inner cutout; `SparklineChart` renders with ≥ 2 points; `TimelineChart` renders milestone rows; empty `@data` produces warning + placeholder (no exception); all three are deterministic (two calls → identical output); `BarChart([("Min",10),("Max",100),("Mid",50)])` Y-axis maximum is 120 (10% headroom above 100); `DonutChart` sectors use `var(--color-primary)` and `var(--color-accent)` (cycling); `TimelineChart` dot color is `var(--color-primary)`; individual chart render call for each new type completes in < 10 ms — confirm ALL FAIL
- [X] T021 [P] [US2] Write integration test in `tests/integration/test_build_phase2.py`: build 4-slide deck (bar + donut + sparkline + timeline) via real temp dir; assert 4 SVG chart elements in output; assert no external URLs; assert bar SVG is identical across two builds — confirm FAILS
- [X] T022 [P] [US2] Generate and commit static fixture `tests/fixtures/expected_bar_chart.svg` by running once: `python -c "from aio.visuals.dataviz.charts import render_chart; from aio.visuals.dataviz.data_parser import parse_chart_data; open('tests/fixtures/expected_bar_chart.svg','w').write(render_chart(parse_chart_data('Q1:50,Q2:75', chart_type='bar')))"` — this file is committed to git and the T021 determinism test compares two fresh renders to this baseline

### Implementation for User Story 2

- [X] T023 [US2] Add `DonutChart(BaseChart)` class to `src/aio/visuals/dataviz/charts.py` with `inner_radius_ratio: float = 0.55` and `center_label: str | None`; render sectors identical to PieChart but clipped by inner white circle; default center_label to `"{n} items"`; cycle sector colors through `["var(--color-primary)", "var(--color-accent)", "var(--color-neutral-500)", ...]` with hex fallbacks matching `_PALETTE` (donut is radial — no Y-axis auto-scaling applies)
- [X] T024 [US2] Add `SparklineChart(BaseChart)` class to `src/aio/visuals/dataviz/charts.py` with `width=200, height=40, color="var(--color-primary)", fill_opacity=0.15`; render `<polyline>` + filled `<path>`; add `display:inline-block;vertical-align:middle` via `style` attribute
- [X] T025 [US2] Add `TimelineChart(BaseChart)` class to `src/aio/visuals/dataviz/charts.py`; parse multi-line `@data` as `date: event` pairs; render vertical dot+connector+label SVG; dots use `var(--color-primary)` (hex fallback `#4C72B0`), connector uses `var(--color-neutral-300)` (hex fallback `#d1d5db`), date label uses `var(--color-neutral-500)` (hex fallback `#6b7280`), event label uses `var(--color-text)` (hex fallback `#1f2937`); cap at 50 events with trailing "…N more" label (timeline is event-positioned — no Y-axis auto-scaling applies)
- [X] T026 [US2] Extend `render_chart()` factory in `src/aio/visuals/dataviz/charts.py` to dispatch `"donut"`, `"sparkline"`, `"timeline"` to new classes
- [X] T027 [US2] Extend `parse_chart_data()` in `src/aio/visuals/dataviz/data_parser.py` to handle: flat numeric CSV (sparkline), multi-line `date: event` format (timeline), return empty `ChartData` + log warning for malformed input
- [X] T028 [US2] Extend `compose_slides()` in `src/aio/commands/build.py` to resolve `metadata.get("chart")` + `metadata.get("data")` (new HTML comment keys) alongside existing `"chart-type"` / `"chart-data"` YAML keys; call `render_chart()`; store result in `SlideRenderContext.chart_svg`; apply `sanitize_svg()` to output
- [X] T029 [US2] When both `@layout` and `@chart` are present on the same slide, log warning "Slide N: both @layout and @chart specified. Chart takes precedence." and clear the layout directive in `SlideRenderContext`
- [X] T030 [US2] Confirm T020, T021 tests now PASS

**Checkpoint**: All four new chart types render inline SVG; old chart types untouched; determinism verified.

---

## Phase 5: User Story 3 — CSS Decorations per Theme (Priority: P3)

**Goal**: Theme `DESIGN.md` section 12 is optionally parsed into `DecorationSpec` records and emitted as `.decoration-*` CSS classes in the output `<style>` block; `<!-- @decoration: gradient -->` applies the class to the slide `<section>`.

**Independent Test**: Add section 12 to a test copy of the `minimal` theme `DESIGN.md`. Build a slide with `<!-- @decoration: gradient -->` via real temp dir. Assert `<section` in output carries `decoration-gradient-primary`. Assert output CSS contains `.decoration-gradient-primary`. Assert no external URLs. Build same deck without section 12 → assert default decoration CSS is present.

### Tests for User Story 3 ⚠️ Write first — confirm FAIL before implementing

- [X] T031 [P] [US3] Write unit tests in `tests/unit/test_decorations.py`: `parse_design_md()` with section 12 returns `DecorationSpec[]`; missing section 12 returns `[]` (no error); CSS generation produces `.decoration-gradient-primary { background: ... }` from spec; `decorations: false` config suppresses all classes — confirm ALL FAIL
- [X] T032 [P] [US3] Write integration test in `tests/integration/test_build_phase2.py`: copy `src/aio/themes/minimal/DESIGN.md` to a temp dir and append a section 12 "Decorations" block defining a primary gradient; build a single slide with `<!-- @decoration: gradient -->` using that modified theme via real temp dir; assert `<section` in output carries `decoration-gradient-primary`; assert output `<style>` contains `.decoration-gradient-primary`; assert no external URLs — confirm FAILS

### Implementation for User Story 3

- [X] T033 [US3] Add `DecorationSpec` dataclass to `src/aio/themes/parser.py` (name, css_class, css_value, css_property, responsive_value) per data-model.md
- [X] T034 [US3] Extend `parse_design_md()` in `src/aio/themes/parser.py` to parse optional section 12 "Decorations" → `list[DecorationSpec]`; return `[]` if section absent; add to returned `ThemeRecord` as `decorations: list[DecorationSpec] = field(default_factory=list)`
- [X] T035 [US3] Add `generate_decoration_css(specs: list[DecorationSpec]) -> str` function in `src/aio/themes/parser.py` that emits `.decoration-{name} { {property}: {value}; }` CSS; if `specs` is empty, emit the four default fallback classes from research.md
- [X] T036 [US3] Extend `render_document()` in `src/aio/commands/build.py` to append `generate_decoration_css(theme_record.decorations)` to the inlined `<style>` block
- [X] T037 [US3] Extend `compose_slides()` in `src/aio/commands/build.py` to resolve `metadata.get("decoration")` + optional `metadata.get("decoration-type")`; set `SlideRenderContext.decoration_class`; skip if `config.decorations == False`
- [X] T038 [US3] Pass `SlideRenderContext.decoration_class` to the Jinja2 layout template so the `<section>` element receives the class; update `base.j2` to include `{{ ctx.decoration_class or '' }}` in the section `class` attribute
- [X] T039 [US3] Update `aio theme validate` in `src/aio/commands/theme.py` to accept 11 or 12 DESIGN.md sections without error
- [X] T040 [US3] Confirm T031, T032 tests now PASS

**Checkpoint**: Decorations CSS is generated and applied; themes without section 12 fall back to defaults; `decorations: false` config suppresses all classes.

---

## Phase 6: User Story 4 — Image Enrichment via Pollinations.ai (Priority: P4)

**Goal**: `aio build --enrich` generates per-slide images from Pollinations.ai free API, base64-encodes them, and inlines them in the output HTML with zero external URLs; graceful fallback to placeholder SVG on API failure.

**Independent Test**: Run `aio build --enrich` on `tests/fixtures/slides_phase2.md` with a mocked HTTP response (pre-baked JPEG from `mock_pollinations_response.jpg`). Assert each enriched slide's `<img>` has `src="data:image/jpeg;base64,"`. Assert zero external URLs. Run twice with same input → assert identical output (deterministic seeds). Run with HTTP mock raising `urllib.error.URLError` → assert placeholder SVG used and build completes.

### Tests for User Story 4 ⚠️ Write first — confirm FAIL before implementing

- [X] T041 [P] [US4] Write unit tests in `tests/unit/test_enrich.py`: `EnrichContext` construction with all fields; `infer_prompt(title, body)` truncates to 100 chars and falls back to "Abstract presentation slide" when result < 3 chars; `derive_seed(deck_title, slide_index)` is deterministic (two calls → same int); JPEG validation (`bytes[:3] == b'\xff\xd8\xff'`) rejects invalid bytes → sets `is_placeholder=True` — confirm ALL FAIL
- [X] T042 [P] [US4] Write integration test in `tests/integration/test_build_enrich.py`: mock `urllib.request.urlopen` to return `mock_pollinations_response.jpg` bytes; build with `--enrich`; assert base64 JPEG in output; assert no external URLs; build again → identical HTML (determinism); mock raises `urllib.error.URLError` → assert placeholder SVG used, build succeeds, warning logged; measure total build time with 2-slide deck — assert < 30 s (mark as `@pytest.mark.slow` to skip in CI where network unavailable) — confirm FAILS

### Implementation for User Story 4

- [X] T043 [US4] Create `src/aio/_enrich.py` with `EnrichContext` dataclass (slide_index, prompt, seed, image_bytes, is_placeholder, error_message) per data-model.md
- [X] T044 [US4] Add `infer_prompt(title: str | None, body: str) -> str` to `src/aio/_enrich.py`: concatenate title + first 80 chars of body (stripped of HTML tags via simple regex); truncate to 100 chars; fallback to "Abstract presentation slide" if result < 3 chars
- [X] T045 [US4] Add `derive_seed(deck_title: str, slide_index: int) -> int` to `src/aio/_enrich.py` using `hashlib.sha256` per research.md decision
- [X] T046 [US4] Add `EnrichEngine` class to `src/aio/_enrich.py` with `enrich_all(contexts: list[EnrichContext]) -> list[EnrichContext]`: for each context, build Pollinations URL via `urllib.parse.urlencode`; call `urllib.request.urlopen(url, timeout=30)`; validate JPEG magic bytes; base64-encode result; handle `URLError` + invalid JPEG → set `is_placeholder=True`, log warning; return updated contexts
- [X] T047 [US4] Add `make_placeholder_svg() -> str` to `src/aio/_enrich.py`: returns a < 200-byte SVG grey rectangle with centered "Image unavailable" text
- [X] T048 [US4] Extend `compose_slides()` in `src/aio/commands/build.py` to create `EnrichContext` per slide that has `image_prompt` in its render context (explicit `@image-prompt` or inferred from title+body); store contexts on `BuildResult.enrich_contexts: list[EnrichContext]` (already defined in data-model.md)
- [X] T049 [US4] Add `--enrich` Typer `Option(False)` to `aio build` in `src/aio/commands/build.py`; add `--dry-run` Typer `Option(False)` to `aio build`
- [X] T050 [US4] Wire Step 4.5 in `build_presentation()` in `src/aio/commands/build.py`: if `enrich=True`, import `EnrichEngine` lazily, call `enrich_all()`, then replace placeholder markers in the rendered HTML string with base64 JPEG data URIs or `make_placeholder_svg()`
- [X] T051 [US4] Implement `--dry-run` logic in `src/aio/commands/build.py`: print step names to stderr; return immediately without writing output file; `steps_total` reflects `--enrich` flag
- [X] T052 [US4] Set `BuildResult.enrich_used = True` and `steps_total = 6` when `--enrich` is active in `src/aio/commands/build.py`
- [X] T053 [US4] Confirm T041, T042 tests now PASS

**Checkpoint**: `aio build --enrich` generates and inlines images; fallback to placeholder on API failure; `--dry-run` prints steps without writing output; Art. II guaranteed.

---

## Phase 7: User Story 5 — Unified Build Pipeline Integration (Priority: P5)

**Goal**: All Phase 2 features (icons, charts, decorations, enrichment) compose correctly in the same deck; progress logging reflects step count accurately; no Phase 1 regressions.

**Independent Test**: Build `tests/fixtures/slides_phase2.md` (contains @icon + @chart + @decoration + @image-prompt) without `--enrich`; assert build completes < 2 s; assert all three features are present in output; assert external-URL check passes. Run `pytest tests/` to confirm zero regressions.

### Tests for User Story 5 ⚠️ Write first — confirm FAIL before implementing

- [X] T054 [P] [US5] Write integration test in `tests/integration/test_build_phase2.py` for combined Phase 2 deck: build `slides_phase2.md` with icon + chart + decoration + no enrich; assert all three features in output; assert build time < 2 s; assert no external URLs; assert `--dry-run` completes in < 100 ms and creates no output file — confirm FAILS
- [X] T055 [P] [US5] Write regression test in `tests/integration/test_build_phase2.py`: build a plain Phase 1 deck (no Phase 2 directives); assert output identical in structure to a Phase 1 build (no decoration CSS injected if no @decoration; no icon containers; no chart SVGs) — confirm FAILS

### Implementation for User Story 5

- [X] T056 [US5] Audit step-count and per-operation logging in `src/aio/commands/build.py`: emit `[INFO] Step N/{steps_total}: STEP_NAME` for each pipeline step; use `BuildResult.steps_total` to derive the denominator; Enrich step emits `Step 4.5/6: ENRICH` only when `--enrich` is active; within the Compose step, emit per-slide operation lines at DEBUG level in the form `[DEBUG] Slide N: {operation} {name}... ✓` on success or `✗` on failure (e.g. `Slide 1: icon=sparkles ✓`, `Slide 2: chart=bar ✓`)
- [X] T057 [P] [US5] Verify `sanitize_svg()` is applied to ALL SVG strings inserted by Phase 2 (icon SVGs in compose_slides, chart SVGs in compose_slides, placeholder SVGs from _enrich.py) — add assertion to T054 integration test
- [X] T058 [US5] Run full test suite `pytest tests/ --cov=src/aio --cov-report=term-missing` and confirm coverage did not regress below current baseline; fix any failing existing tests caused by Phase 2 changes
- [X] T059 [US5] Confirm T054, T055 tests now PASS

**Checkpoint**: All user stories compose without conflict; Phase 1 builds are unaffected; coverage baseline maintained.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T060 [P] Add docstrings to all new public functions in `src/aio/_enrich.py`, `src/aio/commands/icons.py`, new methods in `src/aio/visuals/svg/icons.py` and `src/aio/visuals/dataviz/charts.py` (per Art. Technical Constraints — Documentation)
- [X] T061 [P] Run `ruff check src/ tests/` and `ruff format src/ tests/` — fix all lint and format issues
- [X] T062 [P] Run `mypy src/aio/` — resolve all type errors introduced by Phase 2 additions
- [X] T063 Run the Art. II external-URL check script from `CLAUDE.md` on a freshly built Phase 2 deck and confirm PASS
- [X] T064 Add entries to `examples/` (or update existing) with a Phase 2 sample deck demonstrating @icon, @chart, @decoration, and --enrich usage
- [X] T065 Run `pytest tests/ --cov=src/aio --cov-report=term-missing` final time; confirm ≥ 20% line coverage (CI gate); confirm no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — ⚠️ BLOCKS all user story phases
- **Phase 3 (US1 — Icons)**: Depends on Phase 2
- **Phase 4 (US2 — DataViz)**: Depends on Phase 2; independent of Phase 3
- **Phase 5 (US3 — Decorations)**: Depends on Phase 2; independent of Phases 3–4
- **Phase 6 (US4 — Enrichment)**: Depends on Phase 2; independent of Phases 3–5
- **Phase 7 (US5 — Integration)**: Depends on all previous phases (3–6)
- **Phase 8 (Polish)**: Depends on Phase 7

### User Story Dependencies

- **US1 (Icons)**: Independent after Phase 2
- **US2 (DataViz)**: Independent after Phase 2; the `@chart` compose hook runs alongside `@icon` hook but in separate branches of the same compose step
- **US3 (Decorations)**: Independent after Phase 2; touches `themes/parser.py` and `render_document()`, which US1/US2 do not touch
- **US4 (Enrichment)**: Independent after Phase 2; entirely new module `_enrich.py` and a new build flag; no conflicts with US1–US3
- **US5 (Integration)**: Depends on US1–US4 being complete

### Within Each Phase

- Test tasks (T0xx first suffix) MUST be written and confirmed to FAIL before corresponding implementation tasks
- Within a phase, tasks marked [P] have no file-level conflicts and can run concurrently
- Dependencies within phases are implicit: `compose_slides()` extension (icon, chart, decoration) must happen before render/inline tests pass

### Parallel Opportunities

- T001 and T002 (fixtures) run in parallel
- T003 and T007–T008 in Phase 2 can run in parallel after T004 is done
- After Phase 2 completes, Phases 3, 4, and 5 can all start in parallel (different files)
- Phase 6 can also start in parallel with Phases 3–5 (new `_enrich.py` file)
- Within each phase, all [P]-marked tasks have no file conflicts

---

## Parallel Example: Phases 3 + 4 + 5 after Phase 2

```
After Phase 2 completes:

Parallel stream A (US1 — Icons):
  T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019

Parallel stream B (US2 — DataViz):
  T020 → T021 → T022 → T023 → T024 → T025 → T026 → T027 → T028 → T029 → T030

Parallel stream C (US3 — Decorations):
  T031 → T032 → T033 → T034 → T035 → T036 → T037 → T038 → T039 → T040

Parallel stream D (US4 — Enrichment):
  T041 → T042 → T043 → T044 → T045 → T046 → T047 → T048 → T049 → T050 → T051 → T052 → T053

All streams merge at Phase 7 (US5 — Integration):
  T054 → T055 → T056 → T057 → T058 → T059
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T009) — ⚠️ CRITICAL
3. Complete Phase 3: US1 Icons (T010–T019)
4. **STOP and VALIDATE**: `aio icons list --count` ≥ 200; build a slide with `@icon`; verify inline SVG in output
5. Ship icons as an incremental release

### Incremental Delivery

1. Phases 1+2 → parser foundation
2. Phase 3 → icons MVP
3. Phase 4 → DataViz
4. Phase 5 → Decorations
5. Phase 6 → Enrichment (optional, behind `--enrich` flag)
6. Phase 7 → Integration validation
7. Phase 8 → Polish

Each phase adds value without breaking prior phases.

---

## Notes

- TDD is mandatory (Art. IX): write tests first, confirm FAIL, then implement
- Use `CompositionEngine.sanitize_svg()` on ALL SVG strings (icons, charts, placeholder SVGs)
- Use `yaml.safe_load()` only — no `yaml.load()` anywhere
- All imports in new files MUST be absolute (Art. XII)
- No `print()` in production code — use `src/aio/_log.py`
- `from __future__ import annotations` MUST NOT appear in `cli.py` or `serve.py` (Typer constraint)
- Stop at any checkpoint to validate story independently
- Run `ruff check` + `mypy` after each phase
