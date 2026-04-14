# Tasks: SVG Composites & Image Generation API

**Input**: Design documents from `/specs/004-svg-composites-api/`  
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/ ✅  
**Feature Branch**: `feature/004-svg-composites-api` (based on main)

**Organization**: Tasks grouped by user story (P1–P4) to enable independent implementation and testing. TDD mandatory: tests FIRST, confirm fail, then implement.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, test infrastructure, and documentation structure

- [ ] T001 Create directory structure in `src/aio/visuals/svg/` and `src/aio/_enrich.py` scaffolding per plan.md
- [ ] T002 Initialize test directories: `tests/unit/visuals/`, `tests/integration/visuals/`, `tests/fixtures/`
- [ ] T003 [P] Create test fixtures: `tests/fixtures/sample_themes/` (5 themes), `tests/fixtures/sample_deck/` (10-slide marketing deck)
- [ ] T004 [P] Create mock Pollinations/OpenAI/Unsplash API responses in `tests/fixtures/mock_api_responses/`
- [ ] T005 Create `.aio/cache/` directory structure stub in `.aio/config.yaml` with `parallel_requests: 4` default

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models, interfaces, and infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: Phase 2 MUST complete before any user story work begins

- [ ] T006 Create `VisualStyleConfig` dataclass in `src/aio/visuals/svg/composites.py`: fields for visual_style_preference, pattern, curvature, animation_preference per spec data-model
- [ ] T007 Create `SVGComposite` dataclass in `src/aio/visuals/svg/composites.py`: type, theme_id, style_config, dimensions, svg_content, seed
- [ ] T008 Create `EnrichContext` dataclass in `src/aio/_enrich.py`: slide_index, prompt, seed, image_bytes, is_placeholder, provider_used, error_message
- [ ] T009 Create `CacheEntry` dataclass in `src/aio/_enrich.py`: hash, timestamp, size_bytes, aio_version
- [ ] T010 [P] Create abstract `ImageProvider` base class in `src/aio/_enrich.py` with interface: check_api(), generate(prompt) → bytes
- [ ] T011 [P] Create cache management functions in `src/aio/_enrich.py`: cache_get(), cache_set(), cache_invalidate() using SHA256 keys
- [ ] T012 Create `VisualsException` in `src/aio/exceptions.py` for SVG/visual pipeline errors
- [ ] T013 [P] Implement `.aio/meta.json` metadata structure (cache version tracking) in `src/aio/_utils.py`

**Checkpoint**: All foundational entities and interfaces ready for user story implementation

---

## Phase 3: User Story 1 — SVG Composite Engine (Priority: P1) 🎯 MVP

**Goal**: Render 8 deterministic SVG compositions matching theme palettes, no external APIs needed

**Independent Test**: Verify all 8 SVG types render successfully on all 64 themes with <50ms performance and W3C validity

### Tests for User Story 1 (TDD First)

- [ ] T014 [P] [US1] Unit test for SVG primitives (rect, circle, path) in `tests/unit/visuals/test_svg_primitives.py` — verify color/dimension params
- [ ] T015 [P] [US1] Unit test for gradients and wave patterns in `tests/unit/visuals/test_svg_gradients.py` — verify gradient stops, wave amplitude/frequency
- [ ] T016 [P] [US1] Unit test for deterministic seed-based generation in `tests/unit/visuals/test_svg_determinism.py` — same seed = same SVG
- [ ] T017 [P] [US1] Integration test for all 8 composite types on 5 sample themes in `tests/integration/visuals/test_svg_composites_types.py`
- [ ] T018 [US1] Integration test for SVGComposer fallback on error in `tests/integration/visuals/test_svg_composites_fallback.py`
- [ ] T019 [P] [US1] Visual regression test: SVG→PNG comparison <1% diffs in `tests/visual/test_svg_composites_regression.py` (requires xmllint, imagemagick)

### Implementation for User Story 1

- [ ] T020 [P] [US1] Implement SVG primitives module in `src/aio/visuals/svg/primitives.py`: rect(), circle(), path(), gradient(), wave(), grid() functions
- [ ] T021 [US1] Implement `SVGComposer` class in `src/aio/visuals/svg/composites.py` with compose() method supporting 8 types
- [ ] T022 [US1] Implement hero-background and section-divider types in `src/aio/visuals/svg/composites.py`
- [ ] T023 [US1] Implement feature-illustration and stat-decoration types in `src/aio/visuals/svg/composites.py`
- [ ] T024 [US1] Implement abstract-art, process-steps, comparison-split, grid-showcase types in `src/aio/visuals/svg/composites.py` (post-MVP if needed)
- [ ] T025 [US1] Add error handling and fallback SVG (minimum valid SVG) in `src/aio/visuals/svg/composites.py` — catches all exceptions, returns safe default
- [ ] T026 [US1] Export SVGComposer in `src/aio/visuals/svg/__init__.py` and `src/aio/visuals/__init__.py`
- [ ] T027 [US1] Integrate SVGComposer into composition pipeline: update `src/aio/composition/engine.py` to call compose() in step 2 (analyze_slides phase)
- [ ] T028 [US1] Add logging for SVG composite generation in `src/aio/visuals/svg/composites.py` using `src/aio/_log.py`
- [ ] T029 [P] [US1] Add CLI flag `--svg-only` (optional, non-blocking) to disable image enrichment for MVP testing

**Checkpoint**: User Story 1 complete. Run `pytest tests/unit/visuals/ tests/integration/visuals/` — all must pass. Test with `aio build sample-deck.md` — no external APIs called, all slides have SVG composites.

---

## Phase 4: User Story 2 — Image Generation API Engine (Priority: P2)

**Depends on**: Phase 2 (Foundational) ✓

**Goal**: Generate images via Pollinations (free) → OpenAI (paid, opt-in) → Unsplash (free, opt-in) → SVG fallback; cache results for 95% rebuild speedup

**Independent Test**: Verify Pollinations generates 800×450 JPEG in <8s, cache hit reduces rebuild from 30s→2s, fallback triggers within 500ms on API timeout

### Tests for User Story 2 (TDD First)

- [ ] T030 [P] [US2] Unit test for prompt_builder in `tests/unit/visuals/test_prompt_builder.py` — extract title/bullets/context → coherent prompt
- [ ] T031 [P] [US2] Unit test for each ImageProvider in `tests/unit/visuals/test_image_providers.py` — check_api(), mock generate() responses
- [ ] T032 [P] [US2] Unit test for EnrichEngine.identify_enrichable_slides() in `tests/unit/visuals/test_enrich_identify.py` — heuristic classification by slide type/content
- [ ] T033 [P] [US2] Unit test for image validation (JPEG magic bytes) in `tests/unit/visuals/test_image_validation.py`
- [ ] T034 [US2] Integration test for Pollinations provider (real API) in `tests/integration/visuals/test_pollinations_provider.py` — timeout 15s, expects <8s
- [ ] T035 [US2] Integration test for OpenAI provider (mock key) in `tests/integration/visuals/test_openai_provider.py` — cost estimation, budget warning
- [ ] T036 [US2] Integration test for Unsplash provider (mock key) in `tests/integration/visuals/test_unsplash_provider.py` — photo search, retry logic
- [ ] T037 [US2] Integration test for EnrichEngine fallback chain in `tests/integration/visuals/test_enrich_fallback.py` — Pollinations timeout → OpenAI → Unsplash → SVG
- [ ] T038 [P] [US2] Integration test for data-URI base64 embedding in `tests/integration/visuals/test_enrich_embedding.py` — verify <3 MB total for 10-slide deck

### Implementation for User Story 2

- [ ] T039 [P] [US2] Create `PollinationsProvider` in `src/aio/_enrich.py`: check_api(), generate() using requests.get() to image.pollinations.ai
- [ ] T040 [P] [US2] Create `OpenAIProvider` in `src/aio/_enrich.py`: check_api(), generate() using openai.Image.create(); cost estimation; budget warning before execution
- [ ] T041 [P] [US2] Create `UnsplashProvider` in `src/aio/_enrich.py`: check_api(), generate() via Unsplash API search (if free tier allows; else stub as lower-priority)
- [ ] T042 [US2] Implement `prompt_builder()` function in `src/aio/_enrich.py`: analyze slide title/body → ~100-char prompt
- [ ] T043 [US2] Implement `identify_enrichable_slides()` in `src/aio/_enrich.py`: heuristic returns True for title/comparison/feature slides, False for content-dense
- [ ] T044 [US2] Implement image validation and JPEG conversion in `src/aio/_enrich.py`: verify magic bytes, resize max 800px, JPEG 85% quality
- [ ] T045 [US2] Implement `enrich_all()` in `src/aio/_enrich.py`: orchestrates provider chain with parallel execution (up to 4 concurrent), timeout 10s per image, 3 retries with backoff
- [ ] T046 [US2] Implement base64 data-URI embedding in `src/aio/_enrich.py`: img_bytes → data:image/jpeg;base64,... for inline HTML
- [ ] T047 [US2] Integrate EnrichEngine into build pipeline: update `src/aio/commands/build.py` step 4 (render_document) to call enrich_all() when --enrich flag present
- [ ] T048 [US2] Add CLI flags in `src/aio/commands/build.py`: `--enrich`, `--image-provider {pollinations|openai|unsplash}` (default: pollinations)
- [ ] T049 [US2] Add logging for enrichment progress in `src/aio/_enrich.py` using `src/aio/_log.py` — log provider selection, timeouts, fallbacks

**Checkpoint**: User Story 2 complete. Run `pytest tests/unit/visuals/ tests/integration/visuals/` — all must pass. Test with `aio build sample-deck.md --enrich` — images generated via Pollinations, cached, rebuild <2s.

---

## Phase 5: User Story 3 — Theme Integration (Priority: P3)

**Depends on**: Phase 2 (Foundational) ✓ + Phase 3 (US1 SVG Composites) ✓

**Goal**: Parse DESIGN.md section 10 for Visual Style Preferences; auto-generate defaults for legacy themes

**Independent Test**: Verify 2+ themes with different section 10 preferences (tech vs organic) generate visually distinct SVG composites

### Tests for User Story 3 (TDD First)

- [ ] T050 [P] [US3] Unit test for DESIGN.md section 10 parser in `tests/unit/themes/test_design_section10_parser.py` — extract Visual Style Preference, Pattern, Curvature, Animation Preference
- [ ] T051 [P] [US3] Unit test for legacy theme auto-defaults in `tests/unit/themes/test_legacy_theme_defaults.py` — missing section 10 → tech/geometric/sharp/static
- [ ] T052 [US3] Integration test for theme_loader.py section 10 integration in `tests/integration/themes/test_theme_section10_loading.py` — reads DESIGN.md, populates theme_metadata['visual_config']
- [ ] T053 [P] [US3] Integration test comparing SVG output across visual configs in `tests/integration/visuals/test_svg_visual_config_impact.py` — tech → grid/rects, organic → waves/curves

### Implementation for User Story 3

- [ ] T054 [P] [US3] Extend `theme_loader.py` to parse DESIGN.md section 10 (if present) into VisualStyleConfig dict in theme_metadata
- [ ] T055 [US3] Create defaults generator in `src/aio/themes/parser.py`: if section 10 absent, auto-create VisualStyleConfig(visual_style_preference="tech", pattern="geometric", curvature="sharp", animation_preference="static")
- [ ] T056 [US3] Update `SVGComposer.compose()` to read and apply visual_config heuristics: tech → straight lines/grids, organic → curves/flows, minimal → sparse, geometric → structured
- [ ] T057 [US3] Validate theme section 10 compliance in `src/aio/commands/theme.py` — `aio theme validate {id}` checks for complete section 10 (or generates defaults)
- [ ] T058 [US3] Add warning logging in theme loader when section 10 is incomplete or absent (but don't fail)

**Checkpoint**: User Story 3 complete. Run `pytest tests/unit/themes/ tests/integration/themes/` — all must pass. Run `aio theme validate linear` — verifies/generates section 10. Verify `aio build sample-deck.md --theme linear --theme dribble` — composites differ visually per section 10.

---

## Phase 6: User Story 4 — Caching & Performance (Priority: P4)

**Depends on**: Phase 2 (Foundational) ✓ + Phase 4 (US2 Image Generation) ✓

**Goal**: Cache images and composites; achieve 95% rebuild speedup; manage cache lifecycle

**Independent Test**: Verify 10-slide deck first build ~30s, second build <2s with cache hit; `aio build --cache-stats` shows 95%+ hit rate

### Tests for User Story 4 (TDD First)

- [ ] T059 [P] [US4] Unit test for cache key generation (SHA256) in `tests/unit/visuals/test_cache_key.py` — same prompt+provider → same hash
- [ ] T060 [P] [US4] Unit test for cache_get/cache_set in `tests/unit/visuals/test_cache_ops.py` — read/write, TTL, version check
- [ ] T061 [P] [US4] Unit test for LRU eviction logic in `tests/unit/visuals/test_cache_eviction.py` — <100 MB limit, removes oldest on overflow
- [ ] T062 [US4] Integration test for cache persistence across builds in `tests/integration/visuals/test_cache_hit.py` — first build caches, second build hits 100%
- [ ] T063 [US4] Integration test for cache invalidation on AIO version change in `tests/integration/visuals/test_cache_invalidation.py`

### Implementation for User Story 4

- [ ] T064 [US4] Extend `src/aio/_enrich.py` cache ops: implement full read/write/delete with LRU eviction logic
- [ ] T065 [US4] Create `.aio/cache/images/` directory structure and `.aio/meta.json` versioning in build initialization
- [ ] T066 [US4] Modify EnrichEngine.enrich_all() to check cache BEFORE calling providers — if hash exists and valid, return cached bytes
- [ ] T067 [US4] Add cache invalidation: if aio_version in meta.json differs from current, clear cache gracefully
- [ ] T068 [US4] Implement LRU cache cleanup in `src/aio/_enrich.py`: if .aio/cache/images/ > 100 MB, remove oldest entries until <50 MB
- [ ] T069 [US4] Add CLI commands in `src/aio/commands/build.py`: `--cache-clear` (all), `--cache-clear-images` (images only), `--cache-stats` (show hit rate, size, age)
- [ ] T070 [US4] Add logging for cache operations: cache hit/miss, eviction, invalidation

**Checkpoint**: User Story 4 complete. Run `pytest tests/unit/visuals/test_cache* tests/integration/visuals/test_cache*` — all must pass. Run first build, second build — confirm <2s. Run `aio build --cache-stats` — shows cache stats.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, visual regression validation, performance optimization, comprehensive testing

- [ ] T071 [P] Run all unit tests: `pytest tests/unit/ --cov=src/aio --cov-report=term-missing` — target ≥20%, aspirational 80%
- [ ] T072 [P] Run all integration tests: `pytest tests/integration/ -v` — all must pass on clean slate
- [ ] T073 [P] Run visual regression suite: `pytest tests/visual/ -v` — SVG→PNG pixel diffs <1%
- [ ] T074 [US1] Add quickstart guide in `specs/004-svg-composites-api/quickstart.md` — SVGComposer usage examples (2–3 code snippets)
- [ ] T075 [US2] Add image generation troubleshooting guide in docs/ — common errors, provider fallback behavior
- [ ] T076 [US3] Add theme section 10 authoring guide in docs/ — how to write DESIGN.md section 10 for custom themes
- [ ] T077 [US4] Document cache management in README.md — when to clear, size limits, TTL
- [ ] T078 [P] Verify all external URL checks pass: `python check_external_urls.py out.html` — exit 0 (Article II compliance)
- [ ] T079 Validate SVG output W3C compliance: `xmllint --noout out.html` — no errors (SC-402)
- [ ] T080 [P] Performance profiling: `pytest tests/integration/ --profile` — SVGComposer <50ms (P95), Pollinations <8s (P95), cache <100ms
- [ ] T081 [P] Code review: Check for print() statements (should use _log.py), relative imports (should be absolute), CLAUDE.md compliance
- [ ] T082 Final validation: Build sample deck with all features: `aio build sample-deck.md --theme linear --enrich --cache-stats` — confirm all metrics met

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: ✅ No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 ✅ — **BLOCKS all user stories**
- **Phase 3 (US1 — SVG Composites)**: Depends on Phase 2 ✅
- **Phase 4 (US2 — Image Generation)**: Depends on Phase 2 ✅; CAN start parallel with US1 once Phase 2 complete
- **Phase 5 (US3 — Theme Integration)**: Depends on Phase 2 + Phase 3 (needs SVGComposer working first)
- **Phase 6 (US4 — Caching)**: Depends on Phase 2 + Phase 4 (needs image generation working first)
- **Phase 7 (Polish)**: Depends on all user stories complete ✅

### User Story Execution Order

**Recommended MVP path (sequential)**:
1. **Phase 2**: Foundational (data models, interfaces)
2. **Phase 3**: US1 (SVG Composites) — independent, no external APIs
3. **Phase 4**: US2 (Image Generation) — builds on Phase 2, independent from US1
4. **Phase 5**: US3 (Theme Integration) — requires US1 working
5. **Phase 6**: US4 (Caching) — optimizes US2
6. **Phase 7**: Polish

**Parallel team path** (if multiple developers):
- Developer 1: Phase 2 + Phase 3 (US1)
- Developer 2: Phase 2 + Phase 4 (US2) — starts after Phase 2 done
- Developer 3: Phase 5 (US3) — starts after US1 done
- Developer 4: Phase 6 (US4) — starts after US2 done
- All: Phase 7 (Polish) — final validation

### Within Each Phase: Sequential Dependencies

**Phase 3 (US1) example**:
```
T014-T019 (tests) — write all FIRST, confirm FAIL
↓
T020 (primitives) — after tests written
↓
T021 (SVGComposer class) — after primitives
↓
T022-T024 (8 types) — after class scaffolding
↓
T025-T029 (integration, logging, CLI) — after core working
```

### Parallel Opportunities Within Phase 3

- **Tests (T014–T019)**: All marked [P] — write in parallel
- **Primitives (T020)**: Single file, no parallelization
- **Types (T022–T024)**: Could run parallel IF structured as separate submodules (but recommend sequential for code cohesion)

---

## Parallel Example: User Story 1 (SVG Composites)

```
PARALLEL (start together after Phase 2):
- T014: Unit test for SVG primitives
- T015: Unit test for gradients/waves
- T016: Unit test for determinism
- T019: Visual regression test

SEQUENTIAL (after tests written):
- T020: Implement primitives
- T021: Implement SVGComposer class
- T022: Implement hero-background, section-divider
- T023: Implement feature-illustration, stat-decoration
- T024: Implement remaining types (abstract-art, process-steps, comparison-split, grid-showcase)
- T025: Error handling & fallback

INTEGRATION (after core complete):
- T026: Export from modules
- T027: Integrate into composition pipeline
- T028: Add logging
- T029: CLI flags (optional)
```

---

## Parallel Example: User Story 2 (Image Generation)

```
PARALLEL (start together after Phase 2):
- T030: Prompt builder unit test
- T031: ImageProvider unit tests
- T032: Identify enrichable slides unit test
- T033: Image validation unit test
- T038: Data-URI embedding integration test

SEQUENTIAL (after unit tests written):
- T034: Pollinations provider integration test
- T035: OpenAI provider integration test (mock)
- T036: Unsplash provider integration test (mock)
- T037: Fallback chain integration test

SEQUENTIAL (after tests written):
- T039–T041: Implement providers (can run parallel if separate files)
- T042: Implement prompt_builder
- T043: Implement identify_enrichable_slides
- T044: Image validation & conversion
- T045: EnrichEngine orchestration
- T046: Base64 embedding
- T047: Build pipeline integration
- T048: CLI flags
- T049: Logging
```

---

## Implementation Strategy

### MVP First (Tiers 1 → 2)

**Tier 1 — Core MVP (Phases 1–4)**:
1. ✅ **Phase 1**: Setup test infrastructure, fixtures
2. ✅ **Phase 2**: Data models, interfaces, cache infrastructure
3. ✅ **Phase 3**: SVG Composites (4 core types: hero-background, feature-illustration, stat-decoration, section-divider)
4. ✅ **Phase 4**: Image Generation (Pollinations + SVG fallback; OpenAI/Unsplash deferred)
5. ✅ **Phase 5**: Theme Integration (section 10 parsing + auto-defaults)
6. ✅ **Phase 6**: Caching (cache_get/set, LRU eviction, cache-clear CLI)

**Tier 2 — Post-MVP** (if MVP validation successful):
- Full 8 SVG composite types (all types in Phase 3)
- OpenAI/Unsplash providers (in Phase 4)
- SVG composite caching (additional to image caching)
- Advanced cache invalidation strategies
- Visual regression suite (comprehensive pixel comparisons)

### Stopping Points for Validation

**Stop after Phase 1**: Verify test structure, fixtures load correctly  
**Stop after Phase 2**: Verify all dataclasses instantiate, no import errors  
**Stop after Phase 3**: Verify SVGComposer generates valid W3C SVG on all 64 themes, <50ms P95  
**Stop after Phase 4**: Verify `aio build --enrich` completes, images cached, rebuild <2s  
**Stop after Phase 5**: Verify theme section 10 parsed, visual config applied to SVG output  
**Stop after Phase 6**: Verify `aio build --cache-stats` shows >95% hit rate  
**Before Phase 7**: Run full test suite, validate coverage ≥20%

---

## Success Criteria Alignment

### Phase 3 → SC-401 to SC-406 (SVG Composites)
- SC-401: All 8 types render without error → **T021–T024 complete + T017 integration test passes**
- SC-402: SVG output W3C valid → **T079 (xmllint validation)**
- SC-403: ≤18 KB avg, ≤25 KB P95 → **T027 integration, measure gzip sizes**
- SC-404: Colors from palette 100% precise → **T016 unit test (hex match)**
- SC-405: Visual diffs <1% → **T019 visual regression test**
- SC-406: <50 ms P95 → **T080 performance profiling**

### Phase 4 → SC-410 to SC-416 (Image Generation)
- SC-410: Pollinations <8s P95 → **T034 integration test**
- SC-411: OpenAI <30s, cost ≤$0.15 → **T035 integration test + T040 cost estimation**
- SC-412: Cache hit 95% faster → **T059–T063 cache tests + T062 cache hit validation**
- SC-414: Fallback <500ms → **T037 fallback chain test**
- SC-415: 10-slide deck <45s (Pollinations), <120s (OpenAI) → **T045 parallel execution (4 concurrent)**
- SC-416: <3 MB final output → **T038 embedding test, measure HTML size**

### Phase 5 → SC-425 to SC-426 (Theme Integration)
- SC-425: All 64 themes with section 10 → **T054–T056 section 10 parsing + auto-defaults**
- SC-426: 100% precision extraction → **T050 unit test**

### Phase 6 → SC-430 to SC-431 (Caching)
- SC-430: 95% rebuild speedup → **T062 cache hit test**
- SC-431: <100 MB cache for 50+ decks → **T068 LRU eviction**

---

## Notes

- **[P]**: Tasks can run in parallel (different files, no strict dependencies)
- **[US1–US4]**: Maps task to user story for traceability
- **TDD mandatory**: Write tests FIRST (T0XX), confirm FAIL, then implement (T0XX)
- Each user story phase should be independently completable and testable before moving to next
- Verify tests pass before declaring phase complete
- Stop at checkpoints to validate story independently
- Avoid: vague tasks, same-file conflicts without clear ordering, cross-story dependencies that break independence
