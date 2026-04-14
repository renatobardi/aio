# Implementation Plan: SVG Composites & Image Generation API

**Feature**: Phase 2.5 — Visual Richness (SVG Composites + Image Generation API)  
**Created**: 2026-04-13  
**Status**: Planning Phase Complete  
**Milestone**: M2.5 (per constitution)

---

## Executive Summary

Phase 2.5 implements two core visual enrichment subsystems:

1. **SVG Composite Engine** (P1): 8 reusable SVG composition types (hero-background, feature-illustration, stat-decoration, section-divider, abstract-art, process-steps, comparison-split, grid-showcase) with deterministic generation from theme palettes and visual preferences.

2. **Image Generation API Engine** (P2–P4): Multi-provider image generation (Pollinations.ai free → OpenAI paid → Unsplash free photo search → SVG fallback) with intelligent prompt building, cache layer, and performance optimization.

**Compliance**: Fully aligned with AIO Constitution Articles I, II, III, VI, VII, IX, XII.

---

## Technical Context

| Component | Decision | Rationale |
|-----------|----------|-----------|
| **Language** | Python 3.12+ | Article I mandate; use `A \| B` unions, `@dataclass`, `match/case` |
| **Distribution** | All 4 modes supported | Article XII: zero-install, zipapp, pyinstaller, pip — absolute imports only |
| **Offline-First** | Data-URI base64 embedding | Article II: no external URLs in output; build fails if detected |
| **Visual Core** | SVGComposer as composition foundation | Article III: visual intelligence non-negotiable |
| **Default Provider** | Pollinations.ai (free, no key) | Article VI: free by default; paid (OpenAI) is opt-in |
| **Core Dependencies** | No new deps for SVG; `pillow` already in `[enrich]` | Article VII: stay within 150 MB core, 250 MB with enrich |
| **Vendor Assets** | Reveal.js 5.x pinned | Article VIII: no upgrade to 6.x |
| **Testing** | TDD: tests before implementation | Article IX: coverage grows toward 80%, current gate 20% |

---

## Constitution Check

| Article | Requirement | Phase 2.5 Status | Notes |
|---------|-------------|-----------------|-------|
| **I** | Python 3.12+ primary | ✅ COMPLIANT | All new modules use modern syntax (unions, dataclass, match) |
| **II** | Offline HTML, no external URLs | ✅ COMPLIANT | Images embedded as base64 via enrich; SVG composites are pure inline |
| **III** | Visual Intelligence core | ✅ COMPLIANT | SVGComposer is composition foundation; 8 types support layout-aware visuals |
| **IV** | Agent-agnostic prompting | ✅ COMPLIANT | Enrich engine uses generic prompt_builder; no agent-specific logic |
| **V** | DESIGN.md section 10 mandatory | ✅ COMPLIANT | Theme Integration (P3) enforces Visual Style Preference + Pattern + Curvature |
| **VI** | Free by default | ✅ COMPLIANT | Pollinations.ai used by default; OpenAI/Unsplash require explicit `--image-provider` |
| **VII** | Minimal dependency stack | ✅ COMPLIANT | No new core deps; `pillow` already in `[enrich]` |
| **VIII** | Reveal.js 5.x pinned | ✅ COMPLIANT | No changes to vendor code |
| **IX** | TDD, coverage grows | ✅ COMPLIANT | Tests for SVGComposer, EnrichEngine, cache layer required |
| **X** | 64+ themes, each with DESIGN.md | ✅ COMPLIANT | Phase 2.5 adds DESIGN.md section 10 parsing; auto-generates defaults for legacy themes |
| **XI** | Agent commands versioned/frozen | ✅ COMPLIANT | Enrich engine uses generic prompt; no agent-specific templates |
| **XII** | 4 distribution modes identical | ✅ COMPLIANT | All imports absolute; no sys.path hacking |

**Status**: ✅ **GATE PASSED** — No constitution violations. Phase 2.5 is architecturally sound.

---

## Phase 0: Research & Clarification

**Status**: ✅ **COMPLETE** (via `/speckit.clarify`)

Clarifications resolved:
- Q1: Visual regression testing via SVG→PNG pixel comparison (<1% diffs)
- Q2: All 8 SVG composite types in Phase 2.5 (not phased)
- Q3: Legacy theme migration via auto-generated defaults (tech/geometric/sharp)
- Q4: Third provider = Unsplash (photo search API, free tier)

No unresolved technical questions remain.

---

## Phase 1: Design & Contracts

### 1. Data Model (`data-model.md`)

**Core Entities**:

- **SVGComposite**
  - `type: Literal["hero-background", "feature-illustration", ...]` (8 types)
  - `theme_id: str` (reference to theme)
  - `style_config: VisualStyleConfig` (from DESIGN.md section 10)
  - `dimensions: tuple[int, int]` (width, height; default 1920×1080)
  - `svg_content: str` (valid W3C SVG)
  - `seed: int` (deterministic generation)

- **EnrichContext**
  - `slide_index: int`
  - `prompt: str` (inferred from slide title + body)
  - `seed: int` (hash of deck_title:slide_index for reproducibility)
  - `image_bytes: bytes | None` (JPEG payload)
  - `is_placeholder: bool` (fallback SVG used)
  - `provider_used: Literal["pollinations", "openai", "unsplash", "svg"]`
  - `error_message: str | None` (if fallback triggered)

- **ImageProvider** (abstract base)
  - Interface: `check_api() → bool`, `generate(prompt: str) → bytes`
  - Implementations: `PollinationsProvider`, `OpenAIProvider`, `UnsplashProvider`

- **CacheEntry**
  - `hash: str` (SHA256 of prompt + provider_name)
  - `timestamp: datetime`
  - `size_bytes: int`
  - `aio_version: str` (for cache invalidation on breaking changes)

- **VisualStyleConfig**
  - `visual_style_preference: Literal["geometric", "organic", "tech", "minimal"]`
  - `pattern: Literal["grid", "dots", "lines", "mesh", "noise", "flowing"]`
  - `curvature: Literal["sharp", "soft", "mixed"]`
  - `animation_preference: Literal["static", "subtle", "dynamic"]`

**Relationships**:
- Theme → VisualStyleConfig (1-to-1; auto-generated defaults if absent)
- SVGComposite → Theme (via theme_id)
- EnrichContext → ImageProvider (via provider_used)
- CacheEntry → EnrichContext (via hash; deterministic mapping)

**State Transitions**:
- EnrichContext: **pending** → **generating** → **cached** or **fallback** → **embedded**
- SVGComposite: **requested** → **rendering** → **validated** → **inlined**

---

### 2. Interface Contracts (`contracts/svg-composites.md`, `contracts/image-generation.md`)

**SVGComposer Interface**:
```
compose(
  composite_type: str,
  theme: ThemeRecord,
  dimensions: tuple[int, int] = (1920, 1080),
  seed: int | None = None
) → str  # Returns valid SVG or raises VisualsException
```

**ImageProvider Interface**:
```
generate(
  prompt: str,
  width: int = 800,
  height: int = 450,
  seed: int | None = None
) → bytes  # JPEG payload
```

**Enrich Engine Interface**:
```
enrich_all(
  contexts: list[EnrichContext],
  providers: list[str] = ["pollinations", "openai", "unsplash"],
  timeout_per_image: int = 10,
  parallel_requests: int = 4
) → list[EnrichContext]
```

---

### 3. CLI Contracts (`contracts/cli-flags.md`)

**New/Enhanced Flags**:
- `--enrich` (existing): Enable image generation during build
- `--image-provider {pollinations|openai|unsplash}` (new): Choose primary provider
- `--cache-clear` (new): Clear all caches (`.aio/cache/`)
- `--cache-clear-images` (new): Clear image cache only
- `--cache-stats` (new): Show cache hit rate, size, age

---

### 4. Agent Context Update

No agent-specific logic required for Phase 2.5. Enrich engine uses generic `prompt_builder` (not agent-templated).

**File to update**: `.specify/memory/agent-context-claude.md` — add notes on SVGComposer availability and image generation workflow (informational, not actionable).

---

## Architecture Decisions

### SVGComposer (Composition Layer)

**Location**: `src/aio/visuals/svg/composites.py` (currently stub; fill with 8 types)

**Primitives**:
- `rect(x, y, w, h, fill, opacity)` — filled rectangle
- `circle(cx, cy, r, fill)` — filled circle
- `path(d, stroke, fill, stroke_width)` — SVG path command
- `gradient(type: "linear"|"radial", stops: list[tuple[offset, color]], angle)` — gradient definition
- `wave(width, height, amplitude, frequency, color)` — bezier-based wave pattern
- `grid(width, height, cell_size, color, opacity)` — grid pattern

**Generation Strategy**:
1. Infer visual config from theme's DESIGN.md section 10 (or defaults: tech/geometric/sharp)
2. Extract 2–3 colors from theme palette
3. Select composition type (hero-background → wave + gradient; stat-decoration → grid + circles)
4. Render primitives deterministically (seed-based randomness for pattern variation)
5. Return inline SVG `<svg>...</svg>`

**Determinism**: Seed = hash(theme_id + composite_type) ensures reproducibility across builds.

---

### EnrichEngine (Enrichment Layer)

**Location**: `src/aio/_enrich.py` (partially complete; extend with multi-provider)

**Flow**:
1. `identify_enrichable_slides(deck)` → heuristic determines which slides benefit from images (title, comparison, content-light)
2. For each enrichable slide:
   - `prompt_builder(title, body, context)` → ~100-char prompt
   - `derive_seed(deck_title, slide_index)` → deterministic seed for reproducibility
3. `enrich_all(contexts, providers=[...])` → loop through providers, fallback on timeout/error:
   - Try Pollinations (free, no key, timeout 8s)
   - Fall back to OpenAI (if API key available, timeout 30s)
   - Fall back to Unsplash (if API key available, timeout 8s)
   - Final fallback: `SVGComposer.compose("feature-illustration", ...)`
4. Parallel execution: up to 4 concurrent requests (configurable via `.aio/config.yaml` `parallel_requests`)
5. Base64 encode image → data-URI
6. Defer JPEG writes until `inline_assets` passes (prevent orphaned files on ExternalURLError)

**Caching**: 
- Key: `SHA256(prompt + provider_name)`
- Location: `.aio/cache/images/{hash}.jpg`
- Metadata: `.aio/meta.json` tracks cache version, AIO version (invalidate on breaking changes)

---

### Theme Integration (P3)

**Section 10 Parsing**:
- `theme_loader.py` extracts DESIGN.md section 10
- Creates `VisualStyleConfig` dict
- Stores in `theme_metadata['visual_config']`

**Legacy Theme Handling**:
- If section 10 absent: auto-generate defaults (tech/geometric/sharp/static)
- If section 10 present but incomplete: log warning, apply defaults for missing fields
- New themes created post-Phase-2.5 MUST include section 10 (enforced in `theme validate`)

---

## Module Layout

```
src/aio/
├── visuals/
│   ├── svg/
│   │   ├── composites.py          [NEW] 8 composition types + primitives
│   │   ├── icons.py               [EXISTING]
│   │   └── __init__.py            [MODIFY] export render_composite
│   ├── dataviz/                   [EXISTING, unchanged]
│   └── __init__.py
├── composition/
│   ├── engine.py                  [MODIFY] integrate SVGComposer.compose() in step 2
│   └── ...
├── _enrich.py                     [MODIFY] add multi-provider, cache, parallel logic
├── _log.py                        [EXISTING]
├── commands/
│   ├── build.py                   [MODIFY] wire enrich step with parallel_requests config
│   ├── theme.py                   [EXISTING, validate section 10]
│   └── ...
└── themes/
    ├── loader.py                  [MODIFY] parse section 10 → VisualStyleConfig
    └── ...

.aio/
├── config.yaml                    [MODIFY] add parallel_requests: 4
├── cache/
│   ├── images/                    [NEW] image cache (LRU cleanup)
│   └── composites/                [NEW] optional SVG composite cache (not critical for MVP)
└── meta.json                      [MODIFY] track cache metadata + AIO version
```

---

## Implementation Strategy

### MVP Scope (Phase 2.5, Tier 1):

1. **SVGComposer**: Core 4 types (hero-background, section-divider, feature-illustration, stat-decoration) fully working
2. **EnrichEngine**: Pollinations.ai + SVG fallback; OpenAI/Unsplash deferred if needed
3. **Theme Integration**: Section 10 parsing + auto-defaults for legacy themes
4. **Caching**: Image cache only (SVG composite cache deferred)
5. **CLI**: `--enrich`, `--image-provider pollinations`, `--cache-clear`, `--cache-stats`

### Post-MVP (Tier 2):

- Full 8 SVG composite types (if MVP proves responsive)
- SVG composite caching
- Advanced cache invalidation strategies
- OpenAI/Unsplash provider integration

---

## Testing Strategy (TDD)

**Unit Tests** (`tests/unit/`):
- `test_svgcomposer_primitives.py` — rect, circle, path, gradient rendering
- `test_enrichcontext.py` — EnrichContext dataclass, seed derivation
- `test_cache_entry.py` — cache key generation, versioning

**Integration Tests** (`tests/integration/`):
- `test_svgcomposer_all_types.py` — all 8 types render on all 64 themes (visual diffs <1%)
- `test_enrich_engine_fallback.py` — Pollinations → OpenAI → Unsplash → SVG fallback chain
- `test_enrich_cache_hit.py` — cache hit reduces rebuild time 95%
- `test_theme_legacy_migration.py` — legacy themes auto-generate section 10

**Visual Tests** (`tests/visual/`):
- SVG well-formedness validation (xmllint)
- Composite size validation (≤20 KB gzip)
- Image size validation (data-URI <3 MB per deck)

**Fixtures** (`tests/fixtures/`):
- 5 sample themes (minimal, linear, stripe, dribble, vibrant)
- 10-slide marketing deck (typical for enrichment testing)
- Mock Pollinations responses

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| SVGComposer.compose() | <50 ms (P95) | 8 types, all 64 themes |
| Pollinations API | <8 s (P95) | 800×450 image fetch |
| OpenAI DALL-E | <30 s (P95) | depends on queue depth |
| Cache hit | <100 ms | deterministic lookups |
| Full enrich (10-slide deck) | <45s (Pollinations) / <120s (OpenAI) | with parallelization |

---

## Security & Compliance

- **SVG Sanitization**: No `<script>` tags in any SVG (enforce in composites + inlined images)
- **Image Validation**: Verify JPEG magic bytes (0xFF 0xD8 0xFF) before caching
- **API Key Safety**: `$OPENAI_API_KEY` only; never logged or exposed
- **URL Check**: Build fails (exit code 3) if any external URL detected in output
- **Base64 Encoding**: All images embedded; no external CDN links

---

## Deliverables

### Artifacts (End of Phase 2.5):

1. ✅ **spec.md** — Feature specification (COMPLETE)
2. ✅ **plan.md** — This file (architecture decisions)
3. 🔄 **data-model.md** — Entity definitions, relationships
4. 🔄 **contracts/** — SVGComposer, ImageProvider, CLI interfaces
5. 🔄 **research.md** — Technology decisions (none needed; all clarified)
6. 🔄 **src/aio/visuals/svg/composites.py** — SVGComposer implementation
7. 🔄 **src/aio/_enrich.py** — Multi-provider EnrichEngine
8. 🔄 **src/aio/composition/engine.py** — SVGComposer integration
9. 🔄 **src/aio/themes/loader.py** — Section 10 parser
10. 🔄 **tests/** — Unit + integration tests (TDD)
11. 🔄 **docs/** — SVGComposer usage guide, troubleshooting

### Success Criteria (from spec):

- **SC-401–SC-406** (SVG Composites): All 8 types, W3C valid, <20 KB, color precision, <50 ms
- **SC-410–SC-416** (Image Generation): API response times, cache 95% faster, <3 MB final output
- **SC-425–SC-426** (Theme Integration): All 64 themes with section 10, visual config extracted perfectly
- **SC-430–SC-431** (Caching): 95% rebuild speedup, <100 MB cache for 50+ decks

---

## Next Steps

1. Generate `data-model.md` (entity definitions)
2. Generate `contracts/` (interface specifications)
3. Run `/speckit.tasks` to create task breakdown
4. Begin TDD: write tests for SVGComposer primitives
5. Implement SVGComposer core 4 types
6. Extend EnrichEngine with multi-provider logic
7. Integrate theme section 10 parsing
8. Validate against all 64 themes
9. Merge PR, deploy to main

---
