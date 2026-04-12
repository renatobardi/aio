# Tasks: AIO Core Layouts & Theme System (M1)

**Feature**: 002-core-layouts-theme-system
**Branch**: `feat/002-core-layouts-theme-system`
**Total tasks**: 72
**Generated**: 2026-04-11

---

## Dependencies

```
US1 (layouts) ──────────────────────────────────────────────► US5 (build pipeline)
US3 (DESIGN.md parser) ──► US2 (theme import) ──► US4 (theme CLI) ──► US5
                                                                         │
                                                                         ▼
                                                                      US6 (serve)
```

- Phase 3 (US1) is fully independent — can start immediately
- Phase 4 (US2+US3) — US3 parser tasks must complete before US2 import script tasks
- Phase 5 (US4) — requires Phase 4 complete
- Phase 6 (US5) — requires Phase 3 + Phase 4 complete
- Phase 7 (US6) — requires Phase 6 complete

---

## Phase 1: Setup

**Goal**: Add new dependencies and create package scaffolding.

- [x] T001 Add starlette>=0.37, uvicorn[standard]>=0.29, watchdog>=4.0 to [project.dependencies] in pyproject.toml
- [x] T002 Add httpx>=0.27 to [project.optional-dependencies] dev section in pyproject.toml
- [x] T003 Add 10 new exception classes (ExternalURLError, LayoutNotFoundError, LayoutDefinitionError, LayoutRegistryError, RenderValidationError, SlideContextError, DesignSectionParseError, DesignSectionValidationError, ThemeValidationError, BuildResultError) to src/aio/exceptions.py
- [x] T004 Create src/aio/layouts/__init__.py (empty package marker)
- [x] T005 Create src/aio/composition/__init__.py (empty package marker)
- [x] T006 Add *.j2 and *.json entries for src/aio/layouts/ and src/aio/composition/ to [tool.setuptools.package-data] in pyproject.toml so templates are included in all distribution modes

---

## Phase 2: Foundational

**Goal**: Shared infrastructure required by all user stories — base template, layout registry, and test fixtures.

- [x] T007 Create src/aio/layouts/base.j2 — Reveal.js `<section data-layout="{{ layout_id }}">` skeleton with `{% block slide_content %}`, `{% block slide_class %}`, `{% block slide_attrs %}` blocks; escape all inline `</script>` as `<\/script>`
- [x] T008 Implement LayoutTemplate frozen dataclass and LayoutRegistry singleton (lazy, importlib.resources discovery) in src/aio/layouts/registry.py
- [x] T009 Add escape_script(text: str) -> str Jinja2 filter function and register it in a build_jinja_env() factory in src/aio/_utils.py
- [x] T010 Add base64_inline(image_path: Path) -> str function using stdlib base64 + mimetypes (returns data URI string; handles SVG as raw inline) in src/aio/_utils.py
- [x] T011 Create tests/fixtures/slides/sample_all_layouts.md — 10-slide fixture file with one slide per layout type (hero-title, stat-highlight, split-image-text, content-with-icons, comparison-2col, quote, key-takeaways, closing, auto, content) each using correct @layout and @metadata tags
- [x] T012 Create tests/fixtures/themes/fixture_theme/ with DESIGN.md (all 11 sections, minimal valid content), theme.css (--color-primary, --color-bg, --color-text, --font-display, --font-body), layout.css (.layout-hero-title, .layout-content), meta.json
- [x] T012a Define SlideRenderContext and ComposedSlide dataclasses (per data-model.md §4 and §5 field tables and validation rules) in src/aio/composition/metadata.py — must exist in Phase 2 because CompositionEngine.apply_layout() (T024) returns SlideRenderContext and COMPOSE step (T046) produces ComposedSlide

---

## Phase 3: US1 — 8 Core Layouts Production-Ready

**Story goal**: Given any `slides.md` using one of the 8 `@layout:` directives, `aio build` outputs HTML with correct `<section class="layout-{name}">` structure.

**Independent test**: `pytest tests/unit/test_layouts.py tests/unit/test_composition_engine.py`

- [x] T013 [US1] Write tests/unit/test_layouts.py — 8 parametrized smoke tests, one per layout: render template with minimal context, assert `data-layout="{name}"` in output, assert no `<script>` tag, assert output starts with `<section` and ends with `</section>`
- [x] T014 [US1] Write tests/unit/test_composition_engine.py — 9 parametrized inference tests (one per layout type + auto fallback): assert infer_layout(slide) returns correct LayoutType for each pattern; assert unknown layout falls back to CONTENT
- [x] T015 [US1] [P] Create src/aio/layouts/hero_title.j2 — extends base.j2; renders title (h1.hero-title), subtitle (p.hero-subtitle), centered; reads title/subtitle from context vars
- [x] T016 [US1] [P] Create src/aio/layouts/stat_highlight.j2 — extends base.j2; renders stat_value (span.stat), stat_label (p.stat-label), stat_description (p.stat-description); giant font size via CSS class
- [x] T017 [US1] [P] Create src/aio/layouts/split_image_text.j2 — extends base.j2; CSS grid 50/50; left panel uses image_src as background-image (data URI); right panel renders title + body_html
- [x] T018 [US1] [P] Create src/aio/layouts/content_with_icons.j2 — extends base.j2; renders 3-column grid from body_html list items; each item renders icon keyword + title + description
- [x] T019 [US1] [P] Create src/aio/layouts/comparison_2col.j2 — extends base.j2; renders two columns from left_title/left_content/right_title/right_content context vars; distinct border styling via CSS vars
- [x] T020 [US1] [P] Create src/aio/layouts/quote.j2 — extends base.j2; renders blockquote.layout-quote with quote_text and p.quote-author with quote_attribution; large italic with left border accent
- [x] T021 [US1] [P] Create src/aio/layouts/key_takeaways.j2 — extends base.j2; renders unordered list from body_html; prepends ✓ glyph to each list item via CSS ::before
- [x] T022 [US1] [P] Create src/aio/layouts/closing.j2 — extends base.j2; renders title (h1), optional cta_text as .cta-button; centered layout with prominent CTA block
- [x] T023 [US1] Implement LayoutType enum (HERO_TITLE, STAT_HIGHLIGHT, SPLIT_IMAGE_TEXT, CONTENT_WITH_ICONS, COMPARISON_2COL, QUOTE, KEY_TAKEAWAYS, CLOSING, CONTENT) and per-layout SlotSpec dataclasses in src/aio/composition/layouts.py
- [x] T024 [US1] Implement CompositionEngine with infer_layout(slide: SlideAST) -> LayoutType (9-rule priority chain from research.md §5), apply_layout(slide, layout_type) -> SlideRenderContext, and sanitize_svg(svg_text: str) -> str (strip <script> via xml.etree.ElementTree) in src/aio/composition/engine.py

---

## Phase 4: US2 + US3 — Theme System & DESIGN.md Schema

**Story goal**: `aio theme list` shows ≥ 64 themes; `aio init --theme stripe` works; `aio theme validate stripe` exits 0; `aio build` with stripe theme produces CSS containing `--color-primary: #635BFF`.

**Independent test**: `pytest tests/unit/test_theme_parser.py tests/unit/test_theme.py`

### US3 — DESIGN.md Parser (prerequisite tasks, complete before US2 import script)

- [x] T025 [US2] Write tests/unit/test_theme_parser.py — test parse_design_md() with fixture_theme DESIGN.md: assert 11 DesignSection objects returned; assert section numbers 1–11 all present; assert section 2 parsed_data contains hex colors; assert missing-section case raises DesignSectionParseError listing missing numbers
- [x] T026 [US2] Implement DesignSection dataclass (section_number, heading, raw_content, parsed_data, char_count) in src/aio/themes/parser.py
- [x] T027 [US2] Implement parse_design_md(text: str) -> list[DesignSection] using compiled SECTION_RE regex (re.MULTILINE | re.DOTALL) and yaml.safe_load() for fenced ```yaml blocks in src/aio/themes/parser.py
- [x] T028 [US2] Implement extract_css_vars(sections: list[DesignSection]) -> str that produces :root { --color-*: hex; --font-*: name; } CSS from Color Palette and Typography sections in src/aio/themes/parser.py
- [x] T028a [US2] Implement extract_layout_css(sections: list[DesignSection]) -> str that generates `.layout-*` CSS class stubs from Components (§4) and Layout System (§5) sections; each class stub maps semantic tokens to CSS vars (e.g., `.layout-stat-highlight .stat { color: var(--color-accent); }`); used by import script and theme create scaffold in src/aio/themes/parser.py
- [x] T029 [US2] Update src/aio/themes/validator.py — replace stub with call to parse_design_md(); validate all 11 sections non-empty; validate section 2 hex values and section 11 char count ≥ 200; return list[str] of errors

### US2 — Theme System (import script + loader + registry)

- [x] T030 [US2] Write unit tests for ThemeRecord loading in tests/unit/test_theme.py — test ThemeRecord.from_dict() with valid and invalid meta.json; assert ThemeValidationError on missing required color keys; assert path resolution uses base_dir correctly
- [x] T031 [US2] Implement ThemeRecord dataclass with from_dict(d: dict, base_dir: Path) -> ThemeRecord factory, all fields per data-model.md, and validation raising ThemeValidationError on bad data in src/aio/themes/loader.py
- [x] T032 [US2] Update load_registry() in src/aio/themes/loader.py to produce list[ThemeRecord] instead of list[dict]; resolve all paths relative to registry.json location; return partial list (log warning, skip) for entries with missing CSS files
- [x] T033 [US2] Create scripts/import-awesome-designs.py — CLI with --dry-run, --limit N, --output DIR flags; git clone --depth 1 https://github.com/nicholasgasior/awesome-design-md into tempdir (or git pull --ff-only if already cloned); walk for DESIGN.md + .css pairs; validate via parse_design_md(); copy valid themes to src/aio/themes/{slug}/; regenerate meta.json from parsed sections; append to src/aio/themes/registry.json; exit 0 on partial success, exit 1 if zero themes imported
- [ ] T034 [US2] Update .github/workflows/3-sync-themes.yml to add a nightly scheduled job (cron: '0 3 * * *') that runs python scripts/import-awesome-designs.py and commits any changes with message "chore(themes): nightly sync from awesome-design-md"
- [x] T035 [US2] Write integration test in tests/integration/test_theme_e2e.py — test load_registry() returns ≥ 1 theme (fixture_theme); test ThemeRecord css_path and layout_css_path resolve to existing files; test validate_theme('fixture_theme') returns empty list

---

## Phase 5: US4 — Theme CLI

**Story goal**: All 6 theme subcommands (list, search, info, use, show, create) exit 0 with correct output; `--json` outputs parse cleanly; unknown theme ID exits 2.

**Independent test**: `pytest tests/unit/test_theme_cli.py tests/integration/test_theme_e2e.py`

- [x] T036 [US4] Write tests/unit/test_theme_cli.py — test `aio theme list` shows ID/Name/Tags columns; test `--json` output is valid JSON array; test `--filter design-system` reduces result set; test `aio theme search "minimal"` returns Score column ≥ 0.6; test `aio theme use unknown-id` exits 2; test `aio theme use fixture_theme` outside project dir exits 3
- [x] T037 [US4] Update aio theme list in src/aio/commands/theme.py — add --limit (int, default 20), --filter (str, comma-separated tags), --search (str, fuzzy via difflib.SequenceMatcher ratio ≥ 0.6 with id boost +0.1), --json (flag) options; apply filters in order: tag filter → fuzzy search → limit; Rich table with ID/Name/Tags/Source/Description columns
- [x] T038 [US4] Implement aio theme search QUERY in src/aio/commands/theme.py — reuse list logic with --search forced; add Score column (0.0–1.0, two decimal places) sorted descending; --limit default 10; --json emits array with score field
- [x] T039 [US4] [P] Implement aio theme info ID [--json] in src/aio/commands/theme.py — load ThemeRecord by exact id match; print Rich panel with name/id/source/categories/colors/typography/agent-prompt snippet (truncated at 300 chars); --json emits object; exit 2 if not found
- [x] T040 [US4] [P] Implement aio theme show ID [--section N] [--raw] in src/aio/commands/theme.py — load ThemeRecord.design_md_path; Rich Markdown render or raw text; --section N filters to that section number using parse_design_md(); exit 2 if not found; exit 3 if section N out of range 1–11; exit 4 if no DESIGN.md
- [x] T041 [US4] [P] Implement aio theme use ID [--project-dir DIR] in src/aio/commands/theme.py — validate theme exists in global registry (exit 2 if not); check .aio/ dir exists in project_dir (exit 3 if not); copy theme dir to .aio/themes/{id}/; update theme: key in .aio/config.yaml; stdout: "Theme '{id}' activated. Rebuild with: aio build slides.md"
- [x] T042 [US4] Implement aio theme create NAME [--from ID] [--edit] in src/aio/commands/theme.py — validate NAME is [a-z0-9-]+ (exit 4 if invalid); check no collision in .aio/themes/ (exit 3); copy from existing theme if --from given (exit 2 if source not found), else scaffold from blank template files; print file listing; open $EDITOR on DESIGN.md if --edit; log warning if $EDITOR not set

---

## Phase 6: US5 — Build Pipeline v2

**Story goal**: `aio build slides.md -o out.html` runs 5 logged steps, produces a single file, passes the external-URL check, and renders all 8 layouts.

**Independent test**: `pytest tests/integration/test_build_e2e.py`

- [ ] T043 [US5] Write integration tests in tests/integration/test_build_e2e.py — test build of sample_all_layouts.md exits 0; assert out.html exists and is non-empty; assert no external https:// URLs (run _validators.check_external_urls); assert all 8 data-layout values present in output; test --dry-run exits 0 and does not write file; test unknown layout falls back to content with WARNING; test missing image file substitutes SVG placeholder
- [ ] T044 [US5] Define BuildResult and HotReloadEvent dataclasses (per data-model.md §6 and §7 field tables and validation rules) in src/aio/composition/metadata.py; confirm SlideRenderContext and ComposedSlide (defined in T012a) have all fields required by the build pipeline
- [ ] T045 [US5] Implement ANALYZE step as analyze_slides(asts: list[SlideAST], theme: ThemeRecord) -> list[SlideRenderContext] — resolves layout per slide (explicit @layout tag overrides; CompositionEngine.infer_layout() as fallback); logs WARNING for unknown explicit layout IDs and substitutes CONTENT; populates all SlideRenderContext fields in src/aio/commands/build.py
- [ ] T046 [US5] Implement COMPOSE step as compose_slides(contexts: list[SlideRenderContext], env: jinja2.Environment) -> list[ComposedSlide] — renders each slide via env.get_template(layout_id + ".j2").render(**context); validates html_fragment starts with <section and ends with </section>; calls sanitize_svg() on embedded SVG; accumulates warnings in src/aio/commands/build.py
- [ ] T047 [US5] Implement RENDER step as render_document(slides: list[ComposedSlide], theme: ThemeRecord, title: str) -> str — assembles full Reveal.js HTML document: <html><head> with theme.css + layout.css as <style> blocks, Reveal.js vendor JS as <script> block (escape </script>), </head><body class="reveal"><div class="slides">{slide sections}</div></body></html>; reads vendor JS from src/aio/vendor/revealjs/ in src/aio/commands/build.py
- [ ] T048 [US5] Implement INLINE step as inline_assets(html: str, source_dir: Path, serve_mode: bool = False) -> str — substitutes file:// and relative src= paths with base64 data URIs using base64_inline(); inlines @font-face URLs; runs _validators.check_external_urls(html) and raises ExternalURLError (exit 3) on any https:// found; appends SSE client snippet if serve_mode=True in src/aio/commands/build.py
- [ ] T049 [US5] Implement check_external_urls(html: str) -> list[str] in src/aio/_validators.py — returns list of https?:// URLs found in src= or href= attributes; empty list = pass; used by INLINE step
- [ ] T050 [US5] Wire all 5 steps (PARSE → ANALYZE → COMPOSE → RENDER → INLINE) in build() command in src/aio/commands/build.py — log [INFO] "Step N/5: NAME" at each step start with elapsed time; populate BuildResult; on --dry-run skip write and log planned byte count; stdout "Built: {path} ({N} slides, {MB})" on success
- [ ] T051 [US5] Update build() command signature in src/aio/commands/build.py to remove unused --verbose flag (logging handled by --verbose on root CLI) and wire --dry-run to inline step; ensure NO from __future__ import annotations at top of file

---

## Phase 7: US6 — Serve with Hot Reload

**Story goal**: `aio serve slides.md --port 3000` starts on 127.0.0.1:3000; GET / returns 200 HTML; file change triggers SSE reload event to browser within 2 seconds.

**Independent test**: `pytest tests/integration/test_serve_e2e.py`

- [ ] T052 [US6] Write integration tests in tests/integration/test_serve_e2e.py — use httpx.AsyncClient(app=app, base_url="http://test") transport; test GET / returns 200 text/html with Reveal.js content; test GET /__sse__ returns 200 text/event-stream; test body of / contains EventSource script; test graceful shutdown (SIGINT handler cleans up watchdog observer)
- [ ] T053 [US6] Implement Starlette ASGI app factory create_app(source: Path, build_fn: Callable) -> Starlette with GET / and GET /__sse__ routes in src/aio/commands/serve.py; NO from __future__ import annotations; bind to host/port via uvicorn.Config
- [ ] T054 [US6] Implement SSE handler as async generator that yields data: {json}\n\n events; maintains per-connection asyncio.Queue; on connection, send {"type":"connected"} event; loop awaiting queue.get() and forwarding HotReloadEvent as JSON in src/aio/commands/serve.py
- [ ] T055 [US6] Implement watchdog observer integration — create Observer with FileModifiedHandler that calls loop.call_soon_threadsafe(queue.put_nowait, HotReloadEvent(...)) for each connection queue in the broadcast list; start observer in daemon thread; stop on server shutdown in src/aio/commands/serve.py
- [ ] T056 [US6] Implement port collision detection — before starting uvicorn, attempt socket.create_connection((host, port), timeout=0.1); if succeeds, log error "Port {port} is already in use" and raise typer.Exit(code=2) in src/aio/commands/serve.py
- [ ] T057 [US6] Implement graceful SIGINT shutdown — register signal.signal(signal.SIGINT, ...) handler that stops watchdog observer, calls uvicorn server.should_exit = True, and exits cleanly with code 0 in src/aio/commands/serve.py
- [ ] T058 [US6] Update aio serve command signature in src/aio/commands/serve.py — add --host (str, default "127.0.0.1"), --open (bool flag, open browser after start) options; trigger initial build before starting server; exit 3 if initial build fails
- [ ] T059 [US6] Update serve integration test in tests/integration/test_serve_e2e.py — add test for port collision (bind port before test, assert serve exits 2); add test for --host 0.0.0.0 accepted without error

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T060 Update CLAUDE.md Module Map table to add rows for src/aio/layouts/registry.py, src/aio/composition/engine.py, src/aio/composition/layouts.py, src/aio/composition/metadata.py, src/aio/themes/parser.py
- [ ] T061 Update CLAUDE.md Key Paths section to add layouts (.j2 templates location) and composition (engine + metadata) entries
- [ ] T062 Run pytest --cov=src/aio --cov-report=term-missing --cov-fail-under=80 and fix any coverage gaps (add unit tests for uncovered branches in exceptions.py, _validators.py, _utils.py)
- [ ] T063 Run ruff check src/ tests/ and ruff format src/ tests/ and fix all lint issues before PR
- [ ] T064 Run mypy src/aio/ and fix any type errors (focus on new modules: layouts/, composition/, themes/parser.py)
- [ ] T065 Verify the external-URL checker passes on out.html output: python -c "import re,sys; html=open(sys.argv[1]).read(); bad=re.findall(r'(?:href|src)=[\"\'](https?://[^\"\']+)[\"\'']', html); print('FAIL:',bad) if bad else print('PASS')" out.html
- [ ] T066 Create tests/fixtures/expected/hero_title_output.html — run build with hero_title fixture and save snapshot; add test in test_layouts.py asserting output matches snapshot within 5% edit distance
- [ ] T067 Add src/aio/themes/parser.py module to package-data in pyproject.toml and verify import works in zipapp mode via: python -c "import zipfile; z=zipfile.ZipFile('dist/aio.pyz'); print([f for f in z.namelist() if 'parser' in f])"
- [ ] T068 Run full integration test suite (pytest tests/integration/ -v) on clean venv (pip install -e ".[dev]" in fresh dir) to verify no dependency issues introduced in M1
- [ ] T068a Add per-layout render-time assertion to tests/unit/test_layouts.py — using time.perf_counter(), assert each of the 8 layout renders completes in under 10ms (SC-200 gate); run as a separate parametrized test class so it can be skipped in slow CI environments
- [ ] T068b Add import script timing smoke test to tests/integration/test_theme_e2e.py — run `python scripts/import-awesome-designs.py --limit 5 --output /tmp/aio-theme-test/` and assert wall-clock time < 30s (scales to < 2 min for full 64-theme import per SC-212); skip if network not available (pytest.mark.network)

---

## Dependency Graph

```
T001-T006 (Setup) → T007-T012 (Foundation) → Phase 3 (US1) → Phase 6 (US5)
                                            ↗                ↗
                         Phase 4 (US2+US3) → Phase 5 (US4) /
                                                            /
                                               Phase 6 (US5) → Phase 7 (US6)
```

Within Phase 4:
```
T025-T029 (US3 parser) → T030-T035 (US2 import + loader)
```

Within Phase 6 (US5):
```
T012a (SlideRenderContext + ComposedSlide) ──────────────────────────────────────────────────────────► T024 (CompositionEngine)
T044 (BuildResult + HotReloadEvent) → T045 (ANALYZE) → T046 (COMPOSE) → T047 (RENDER) → T048 (INLINE) → T050 (wire all)
T049 (check_external_urls) ──────────────────────────────────────────────────────────► T048
```

---

## Parallel Execution Opportunities

**Phase 3 (US1)** — T015–T022 can all run in parallel (different files):
```
T015 hero_title.j2
T016 stat_highlight.j2     ← all 8 layout .j2 files are independent of each other
T017 split_image_text.j2
T018 content_with_icons.j2
T019 comparison_2col.j2
T020 quote.j2
T021 key_takeaways.j2
T022 closing.j2
```

**Phase 5 (US4)** — T039–T042 can run in parallel (different command implementations, same file but different functions):
```
T039 theme info     ← independent of use/show
T040 theme show     ← independent of info/use
T041 theme use      ← independent of info/show
```

**Phase 6 (US5)** — T045–T048 must be sequential (each step's output feeds the next).

---

## Implementation Strategy (MVP First)

**MVP = Phase 1 + Phase 2 + Phase 3 (US1)**

To validate the layout system works end-to-end before tackling the full theme import:
1. Complete Setup (T001–T006)
2. Complete Foundation (T007–T012)
3. Complete US1 (T013–T024) — 8 layouts + inference engine
4. Run: `aio build tests/fixtures/slides/sample_all_layouts.md -o /tmp/out.html`
   - This will fail on INLINE step (stub) but COMPOSE output can be verified
5. Ship US1 as independently testable increment

**Full M1 delivery order:**
Phase 1 → Phase 2 → Phase 3 → Phase 4 (US3 tasks first) → Phase 5 → Phase 6 → Phase 7 → Phase 8
