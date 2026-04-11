# Implementation Plan: AIO Core Layouts & Theme System (M1)

**Branch**: `002-core-layouts-theme-system` | **Date**: 2026-04-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification — 6 user stories (P1–P6), 58 FRs (FR-200–FR-257)

## Summary

M1 delivers the full visual foundation of AIO: 8 Jinja2 layout templates wired through an inference engine, a theme system seeded from 64+ real-world DESIGN.md files imported via a bootstrap script, and a complete theme CLI with fuzzy search. It also replaces the M0 build stub with a deterministic 5-step pipeline and adds Starlette-based hot-reload serving via SSE. All deliverables are additive — no M0 API surfaces are broken.

---

## Technical Context

| Attribute | Value |
|-----------|-------|
| Language | Python 3.12+ (3.10+ tolerated) |
| New runtime deps | `starlette`, `uvicorn[standard]` (serve only); `watchdog` (hot-reload) |
| New optional deps | `pillow` (image inlining, already in `[enrich]`) |
| Storage | `.aio/` project config dir; `src/aio/themes/{id}/` for bundled themes |
| Testing | pytest, real temp dirs for core pipeline, no `unittest.mock` for build/compose |
| Platform | macOS / Linux primary; Windows accepted via pip |
| Performance targets | Build 30 slides < 30s; serve hot-reload < 2s; parse 100 slides < 500ms; `aio theme list` < 1s |
| New module boundaries | `src/aio/layouts/` owns .j2 templates; `src/aio/composition/` owns inference; `src/aio/themes/` extended with parser/importer; `src/aio/commands/` extended with serve ASGI + updated theme/build |

---

## Constitution Check

*GATE: All 12 articles evaluated.*

| Article | Gate | M1 Status |
|---------|------|-----------|
| **Art. I** — Python 3.12+ | `A \| B` unions used; no `typing.Union`; walrus/match where applicable | ✅ PASS — all new code targets 3.12+; annotations use `X \| None` syntax throughout |
| **Art. II** — Offline HTML | `inline()` step raises `ExternalURLError` (exit 3) on any `https?://` in output | ✅ PASS — build test asserts zero external refs in all layout fixture outputs |
| **Art. III** — Visual Intelligence | All slides pass through `CompositionEngine.infer_layout()` | ✅ PASS — inference is mandatory in ANALYZE step; bypassing it requires explicit `--no-compose` (not exposed in M1) |
| **Art. IV** — Agent-Agnostic | No agent-specific code in layouts or theme system | ✅ PASS — layouts and themes are agent-neutral; agent command templates are read in COMPOSE step via existing `agents/prompts.py` |
| **Art. V** — DESIGN.md 11-section | `parse_design_md()` validates all 11 sections; `aio theme validate` calls it | ✅ PASS — validator updated; import script rejects themes with < 11 sections |
| **Art. VI** — Free by Default | No paid API calls in M1; Pollinations.ai deferred to `--enrich` flag | ✅ PASS — `--enrich` is opt-in; all layout rendering works without any network call |
| **Art. VII** — Deps < 150 MB | starlette (~500 KB) + uvicorn (~200 KB) + watchdog (~1.5 MB) ≈ +3 MB | ✅ PASS — core budget remains well under 150 MB; size measured in CI with pip aggregate |
| **Art. VIII** — Reveal.js 5.x | Vendor directory untouched; `</script>` escape applied in Jinja2 `render()` via `escape_script` filter | ✅ PASS — `escape_script` custom filter registered in Jinja2 env; tested via fixture output assertion |
| **Art. IX** — 80% Coverage | TDD; tests written before implementation; CI gate enforced | ✅ PASS — layout, composition, theme parser, serve SSE all have unit + integration test files |
| **Art. X** — 64+ Themes | Import script targets `nicholasgasior/awesome-design-md`; nightly sync via GitHub Actions | ✅ PASS — registry grows to 64+ on first CI run; `--limit N` flag for bounded test imports |
| **Art. XI** — Versioned Agent Commands | No new agent command versions in M1 | ✅ N/A — agent command prompts unchanged in M1; deferred to M2 |
| **Art. XII** — 4 Distribution Modes | `importlib.resources.files()` used for layout discovery; no `__file__`-relative paths | ✅ PASS — layout and theme file access via importlib.resources; verified in zipapp smoke test |

**Gate result**: **PASS** — all 12 articles satisfied. One watch item: `watchdog` pulls in a native extension on macOS; verify size budget in CI before merge.

---

## Project Structure

### Documentation

```
specs/002-core-layouts-theme-system/
├── plan.md              ← this file
├── spec.md              ← user stories + FRs (FR-200–FR-257)
├── research.md          ← Phase 0 — technology decisions
├── data-model.md        ← Phase 1 — entity definitions
├── quickstart.md        ← Phase 1 — developer setup
├── contracts/
│   └── cli-contract.md  ← Phase 1 — CLI contracts for new/changed commands
└── checklists/
    ├── requirements.md  ← FR checkboxes (58 items)
    └── ux.md            ← UX acceptance criteria
```

### New Source Code for M1

```
src/aio/
├── cli.py                              (updated: register serve hot-reload, extract_design)
├── commands/
│   ├── build.py                        (updated: 5-step pipeline v2)
│   ├── init.py                         (unchanged)
│   ├── theme.py                        (updated: search/info/use/show/create implemented)
│   ├── serve.py                        (updated: Starlette ASGI + SSE hot reload)
│   ├── extract.py                      (unchanged stub)
│   └── commands.py                     (unchanged)
├── layouts/
│   ├── __init__.py
│   ├── registry.py                     (NEW: LayoutRegistry, importlib.resources discovery)
│   ├── base.j2                         (NEW: Reveal.js section skeleton, escape_script)
│   ├── hero_title.j2                   (NEW)
│   ├── stat_highlight.j2               (NEW)
│   ├── split_image_text.j2             (NEW)
│   ├── content_with_icons.j2           (NEW)
│   ├── comparison_2col.j2              (NEW)
│   ├── quote.j2                        (NEW)
│   ├── key_takeaways.j2                (NEW)
│   └── closing.j2                      (NEW)
├── composition/
│   ├── __init__.py
│   ├── engine.py                       (NEW: CompositionEngine, infer_layout(), apply_layout())
│   ├── layouts.py                      (NEW: LayoutType enum, 8 layout dataclasses)
│   └── metadata.py                     (NEW: SlideMetadata, ComposedSlide, BuildResult)
├── themes/
│   ├── loader.py                       (updated: ThemeRecord.from_dict(), path resolution)
│   ├── validator.py                    (updated: full 11-section schema via parse_design_md)
│   ├── parser.py                       (NEW: parse_design_md(), DesignSection dataclass)
│   ├── registry.json                   (updated: 64+ imported themes after bootstrap)
│   └── {id}/                           (64+ theme dirs)
│       ├── DESIGN.md
│       ├── theme.css
│       ├── layout.css
│       └── meta.json
├── vendor/
│   └── revealjs/                       (unchanged: 5.x UMD build)
├── _log.py                             (unchanged)
├── _validators.py                      (updated: external-URL checker used in inline() step)
├── _utils.py                           (updated: escape_script Jinja2 filter, base64_inline())
└── exceptions.py                       (updated: ExternalURLError, LayoutNotFoundError,
                                                   LayoutDefinitionError, LayoutRegistryError,
                                                   RenderValidationError, SlideContextError,
                                                   DesignSectionParseError, DesignSectionValidationError,
                                                   ThemeValidationError, BuildResultError)

scripts/
└── import-awesome-designs.py          (NEW: git clone + DESIGN.md harvest + registry update)

tests/
├── unit/
│   ├── test_layouts.py                 (NEW: 8 layout render smoke tests)
│   ├── test_composition_engine.py      (NEW: infer_layout() parametrized per layout type)
│   ├── test_theme_parser.py            (NEW: parse_design_md() with fixture DESIGN.md)
│   ├── test_theme_cli.py               (updated: search/info/use/show/create)
│   └── test_build.py                   (updated: 5-step pipeline unit assertions)
├── integration/
│   ├── test_build_e2e.py               (updated: full pipeline, external-URL assertion)
│   └── test_serve_e2e.py               (updated: SSE endpoint, httpx transport)
└── fixtures/
    ├── slides/sample_all_layouts.md    (NEW: one slide per layout type)
    ├── themes/fixture_theme/           (NEW: minimal valid theme for tests)
    └── expected/hero_title_output.html (NEW: snapshot for layout regression)
```

---

## Phases

### Phase 1 — Layout Engine (US1)

**Goal**: 8 Jinja2 templates + inference engine wired into a testable `CompositionEngine`.

**Implementation order**:
1. Define `LayoutType` enum and 8 layout dataclasses in `src/aio/composition/layouts.py`.
2. Write `src/aio/layouts/base.j2` (Reveal.js section wrapper, `data-layout` attribute, no external URLs).
3. Write each `.j2` template extending `base.j2`; run manual smoke test with `jinja2.Environment`.
4. Implement `CompositionEngine.infer_layout(slide: SlideAST) -> LayoutType` — priority chain from research.md §5.
5. Implement `apply_layout(slide, layout_type) -> str` (renders template with slide vars).
6. Write tests: `test_composition_engine.py` — one parametrized case per layout type; assert `data-layout="{name}"` and no `<script>` in SVG blocks.

**Key dependencies**: Jinja2 (M0), `xml.etree.ElementTree` (stdlib) for SVG sanitize.

**Done when**: `pytest tests/unit/test_layouts.py tests/unit/test_composition_engine.py` green; no external URLs in any rendered layout fixture.

---

### Phase 2 — Theme System (US2 + US3)

**Goal**: 64+ themes importable from awesome-design-md; DESIGN.md 11-section parser.

**Implementation order**:
1. Write `scripts/import-awesome-designs.py`:
   - `subprocess.run(["git", "clone", "--depth=1", REPO_URL, tmp_dir], check=True)` — no gitpython.
   - Walk cloned dir for `DESIGN.md` files; validate 11 sections present.
   - Copy valid themes to `src/aio/themes/{slug}/`; generate `meta.json` from sections 1–3.
   - Append entries to `src/aio/themes/registry.json`.
   - `--dry-run` flag: print what would be imported without writing files.
   - `--limit N` flag for CI (import N themes to keep test runtime bounded).
2. Implement `src/aio/themes/parser.py`: `parse_design_md(path) -> list[DesignSection]` using compiled `SECTION_RE` regex + `yaml.safe_load()`.
3. Update `src/aio/themes/validator.py` to call `parse_design_md()` and assert all 11 sections non-empty.
4. Update `src/aio/themes/loader.py` to produce `ThemeRecord` instances from registry.json with path resolution.

**Key dependencies**: stdlib `subprocess`, `pathlib`, `re`, `json`. No new deps.

**Done when**: `python scripts/import-awesome-designs.py --dry-run` exits 0; `pytest tests/unit/test_theme_parser.py` green with fixture DESIGN.md covering all 11 sections.

---

### Phase 3 — Theme CLI (US4)

**Goal**: Complete `aio theme` command group — list (updated), search, info, use, show, create.

**Implementation order**:
1. `theme list`: add `--search QUERY` (fuzzy via `difflib.SequenceMatcher`), `--filter TAGS`, `--limit N`, `--json` output.
2. `theme search QUERY`: ranked table with `Score` column (0.0–1.0).
3. `theme info ID`: parse `meta.json` + first 3 DESIGN.md sections; print Rich panel; `--json` flag.
4. `theme use ID`: copy theme dir to `.aio/themes/{id}/`; update `.aio/config.yaml` `theme` key; exit 3 if no `.aio/`.
5. `theme show ID [--section N]`: pretty-print DESIGN.md in Rich Markdown with optional section filter.
6. `theme create NAME [--from ID]`: scaffold new theme dir from blank template or existing theme.

All commands respect `--json` for machine-readable output. All output via Rich console or `_log.py`.

**Key dependencies**: `difflib` (stdlib), `rich` (M0).

**Done when**: `pytest tests/unit/test_theme_cli.py` green; `aio theme list --json | python -m json.tool` exits 0.

---

### Phase 4 — Build Pipeline v2 (US5)

**Goal**: Replace M0 stub with deterministic 5-step pipeline.

**Steps**:
```
PARSE   → parse_slides(md_path)        → SlideAST[]
ANALYZE → analyze_slides(asts)         → SlideMetadata[] (title, word count, layout hints)
COMPOSE → compose_slides(metas)        → ComposedSlide[] (layout inferred, SVG generated)
RENDER  → render_slides(composed)      → HTML fragment per slide (Jinja2 + theme vars)
INLINE  → inline_assets(fragments)     → single .html (CSS/JS/fonts/images embedded, URL check)
```

**Implementation order**:
1. Define `ComposedSlide`, `BuildResult` in `src/aio/composition/metadata.py`.
2. Implement `analyze_slides()` in `commands/build.py` — reads frontmatter `layout:` override; falls back to `infer_layout()`.
3. Implement `render_slides()` — instantiate Jinja2 env with `escape_script` filter; render per-slide HTML.
4. Implement `inline_assets()` — base64-encode images, embed CSS/JS as `<style>`/`<script>`, strip external refs, call `_validators.check_external_urls()`.
5. Wire all 5 steps in `build` command; emit structured log lines per step with timing.
6. Integration test: `test_build_e2e.py` — build `fixtures/slides/sample_all_layouts.md` → assert single HTML file, no external URLs, all 8 `data-layout` values present.

**Key dependencies**: `base64` (stdlib), `pathlib`, `jinja2`, `_validators.py`.

**Done when**: `pytest tests/integration/test_build_e2e.py` green; build of 30-slide fixture completes in < 30s on CI.

---

### Phase 5 — Serve with Hot Reload (US6)

**Goal**: `aio serve slides.md` — live-reload dev server with SSE.

**Architecture**:
- Starlette ASGI app: `GET /` (serve built HTML), `GET /__sse__` (SSE event stream).
- `watchdog.observers.Observer` watches `.md` source file; on change, triggers rebuild and pushes `data: reload\n\n` to all open SSE connections via `asyncio.Queue` + `loop.call_soon_threadsafe`.
- Injected JS snippet: `<script>const es=new EventSource('/__sse__');es.onmessage=()=>location.reload()<\/script>` (escaped per Art. VIII).
- Default bind: `127.0.0.1:{port}`; `--host` flag overrides.
- Graceful shutdown: `SIGINT` stops watchdog observer before exiting event loop.

**Implementation order**:
1. Implement Starlette app factory in `commands/serve.py`; no `from __future__ import annotations`.
2. Implement SSE handler using `starlette.responses.StreamingResponse` with `asyncio.Queue`.
3. Wire watchdog observer; on `.md` change call `build_pipeline()` in thread pool via `asyncio.to_thread`.
4. Inject SSE client snippet in `inline_assets()` when `serve_mode=True` (stripped in production builds).
5. Integration test: `test_serve_e2e.py` — use `httpx.AsyncClient(app=app, base_url="http://test")` transport; assert `/` returns 200 with `text/html`; assert `/__sse__` returns `text/event-stream`.

**Key dependencies**: `starlette`, `uvicorn[standard]`, `watchdog`, `anyio` (transitive via starlette).

**Done when**: `pytest tests/integration/test_serve_e2e.py` green; manual edit-save-reload loop < 2s on a 10-slide file.

---

## Dependencies Added in M1

| Package | Version constraint | Extra | Purpose |
|---------|-------------------|-------|---------|
| `starlette` | `>=0.37,<1` | core | ASGI framework for serve |
| `uvicorn[standard]` | `>=0.29,<1` | core | ASGI server |
| `watchdog` | `>=4.0,<5` | core | File-system watcher for hot reload |
| `httpx` | `>=0.27,<1` | dev | Async test client for serve integration tests |

**Removed**: none.

**Size impact**: starlette (~500 KB) + uvicorn (~200 KB) + watchdog (~1.5 MB native) ≈ +3 MB compressed. Core budget remains well under 150 MB (Art. VII).

**Note**: `gitpython` is explicitly rejected. The import script uses `subprocess.run(["git", ...], check=True)`. Git must be present in PATH (documented in quickstart.md).
