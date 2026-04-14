# Data Model: SVG Composites & Image Generation API

**Feature**: Phase 2.5 — Visual Richness  
**Created**: 2026-04-13  
**Status**: Complete  
**Source**: plan.md § Architecture Decisions

---

## Core Entities

### SVGComposite

Represents a rendered SVG composition for a slide.

```python
@dataclass
class SVGComposite:
    type: Literal[
        "hero-background",
        "feature-illustration",
        "stat-decoration",
        "section-divider",
        "abstract-art",
        "process-steps",
        "comparison-split",
        "grid-showcase"
    ]
    theme_id: str                      # Reference to theme
    style_config: VisualStyleConfig    # From DESIGN.md section 10
    dimensions: tuple[int, int]        # (width, height); default 1920×1080
    svg_content: str                   # Valid W3C SVG
    seed: int | None                   # Deterministic generation seed
```

**Relationships**:
- Theme → SVGComposite (via theme_id)
- VisualStyleConfig → SVGComposite (via style_config)

**Validation Rules**:
- `type` must be one of 8 supported compositions
- `svg_content` must be valid W3C SVG (no `<script>` tags)
- `dimensions` must be positive integers
- `seed` is optional; if present, same seed + type + theme → same SVG

**State Transitions**:
- **requested** → **rendering** (SVGComposer.compose() called)
- **rendering** → **validated** (W3C check passes)
- **validated** → **inlined** (embedded in HTML as `<svg>...</svg>`)
- **any** → **fallback** (error occurred; minimum valid SVG returned)

---

### VisualStyleConfig

Extracted from DESIGN.md section 10; controls SVG composition styling.

```python
@dataclass
class VisualStyleConfig:
    visual_style_preference: Literal["geometric", "organic", "tech", "minimal"]
    pattern: Literal["grid", "dots", "lines", "mesh", "noise", "flowing"]
    curvature: Literal["sharp", "soft", "mixed"]
    animation_preference: Literal["static", "subtle", "dynamic"]
```

**Relationships**:
- Theme → VisualStyleConfig (1-to-1, stored in theme_metadata['visual_config'])

**Validation Rules**:
- All fields must be one of allowed literals
- Required in all themes; auto-generated defaults (tech/geometric/sharp/static) for legacy themes

**Defaults** (for legacy DESIGN.md without section 10):
```python
VisualStyleConfig(
    visual_style_preference="tech",
    pattern="geometric",
    curvature="sharp",
    animation_preference="static"
)
```

**Generation Heuristics**:
- `visual_style_preference="tech"` → straight lines, grid patterns, ≤45° angles
- `visual_style_preference="organic"` → bezier curves, flowing patterns, soft edges
- `visual_style_preference="minimal"` → sparse elements, high contrast
- `visual_style_preference="geometric"` → structured shapes, patterns

---

### EnrichContext

Per-slide state for image generation enrichment.

```python
@dataclass
class EnrichContext:
    slide_index: int                                    # 0-based slide number
    prompt: str                                         # ~100-char inferred prompt
    seed: int                                           # hash(deck_title + slide_index)
    image_bytes: bytes | None = None                    # JPEG payload (if generated)
    is_placeholder: bool = False                        # True if using SVG fallback
    provider_used: Literal[
        "pollinations", "openai", "unsplash", "svg"
    ] = "svg"
    error_message: str | None = None                    # Reason for fallback
```

**Relationships**:
- BuildResult → EnrichContext[] (1-to-many)
- CacheEntry → EnrichContext (via prompt hash)

**Validation Rules**:
- `slide_index` must be non-negative
- `prompt` must be ≥10 chars, ≤200 chars
- `seed` is deterministic: hash(deck_title:slide_index)
- If `is_placeholder=True`, `error_message` must be non-empty
- `image_bytes` is None until successful generation or fallback

**State Transitions**:
- **pending** (created, waiting for enrich_all())
- **generating** (API call in progress)
- **cached** (cache hit found, image_bytes populated)
- **fallback** (API timeout/error; SVG composite generated, is_placeholder=True)
- **embedded** (base64 data-URI created, ready for HTML)

---

### ImageProvider (Abstract)

Base interface for image generation providers.

```python
@dataclass
class ImageProvider:
    api_key: str | None = None
    timeout_seconds: int = 10
    
    def check_api(self) -> bool:
        """Check if API is available and authenticated."""
        raise NotImplementedError
    
    def generate(
        self,
        prompt: str,
        width: int = 800,
        height: int = 450,
        seed: int | None = None
    ) -> bytes:
        """Generate image and return JPEG bytes.
        
        Raises:
            TimeoutError: API call exceeded timeout_seconds
            ValueError: Invalid prompt or parameters
            ConnectionError: Network/authentication failure
        """
        raise NotImplementedError
```

**Concrete Implementations**:

#### PollinationsProvider

**URL**: `image.pollinations.ai?prompt={prompt}&width={width}&height={height}`  
**Authentication**: None (free, no API key)  
**Timeout**: 8s (P95)  
**Features**:
- No API key required
- Returns PNG; converted to JPEG in EnrichEngine
- Deterministic (same seed → same image)

#### OpenAIProvider

**Endpoint**: `POST /v1/images/generations`  
**Authentication**: Bearer $OPENAI_API_KEY  
**Timeout**: 30s (P95)  
**Features**:
- Requires OPENAI_API_KEY env var
- DALL-E 3 model
- Cost: ~$0.08–0.12 per image
- Budget warning before execution
- Requires explicit `--image-provider openai` flag

#### UnsplashProvider

**API**: Unsplash photo search  
**Authentication**: Unsplash API key  
**Timeout**: 8s (P95)  
**Features**:
- Free tier available
- Photo search (not generation)
- Requires `--image-provider unsplash` flag
- Retry 3x with backoff

#### SVGProvider (Fallback)

**Type**: Automatic fallback  
**Mechanism**: SVGComposer.compose("feature-illustration", ...) called on timeout/error  
**Timeout**: <500ms  
**Features**:
- Never fails (always returns valid SVG)
- No external API calls

---

### CacheEntry

Cache metadata and versioning.

```python
@dataclass
class CacheEntry:
    hash: str              # SHA256(prompt + provider_name)
    timestamp: datetime    # When entry was created
    size_bytes: int        # Payload size (for LRU eviction)
    aio_version: str       # Version of AIO that created this entry
```

**Relationships**:
- `.aio/cache/images/{hash}.jpg` ← CacheEntry.hash
- `.aio/meta.json` → CacheEntry[] (metadata registry)

**Validation Rules**:
- `hash` must be 64-char hex (SHA256)
- `aio_version` matches `__version__` in src/aio/__init__.py
- If `aio_version` differs from current, entry is invalidated

**Cache Lifecycle**:
1. **Creation**: CacheEntry written when image successfully generated
2. **Hit**: When `EnrichEngine.enrich_all()` finds matching hash
3. **Eviction**: LRU cleanup removes oldest entries when `.aio/cache/images/` > 100 MB
4. **Invalidation**: If `aio_version` changes, all entries cleared

---

## Aggregate Roots

### BuildResult

Container for all enrichment results from a single `aio build` run.

```python
@dataclass
class BuildResult:
    total_slides: int
    enriched_contexts: list[EnrichContext]
    cache_stats: dict[str, int]  # {"hits": N, "misses": N, "errors": N}
    total_build_time_sec: float
    enrich_time_sec: float | None = None
```

**Responsibilities**:
- Tracks per-slide enrichment state
- Provides cache hit statistics
- Enables rebuild-time optimization analysis

---

## Relationships & Constraints

### Theme → VisualStyleConfig (1:1)

```
src/aio/themes/{theme_id}/DESIGN.md
    ├── section 10 extracted
    └── → theme_metadata['visual_config']  (VisualStyleConfig instance)
```

**Rule**: Every theme has exactly one VisualStyleConfig (auto-generated if section 10 absent).

### Theme → SVGComposite (N:M)

```
SVGComposite.theme_id → Theme.id
SVGComposite.type ∈ {hero-background, ...} (8 types × 64 themes = up to 512 compositions)
```

**Rule**: Each (theme_id, type) pair generates deterministically (same seed → same output).

### EnrichContext → CacheEntry (0:1)

```
EnrichContext.prompt + EnrichContext.provider_used
    → SHA256 hash
    → CacheEntry.hash
    → .aio/cache/images/{hash}.jpg
```

**Rule**: One EnrichContext may have zero or one cache hit.

### EnrichContext → ImageProvider (N:1)

```
EnrichEngine.enrich_all(contexts, providers=[...])
    └── for each context, try providers in order:
        1. PollinationsProvider
        2. OpenAIProvider (if API key present)
        3. UnsplashProvider (if API key present)
        4. SVGProvider (fallback)
```

**Rule**: EnrichContext.provider_used reflects which provider succeeded.

---

## Data Flow Diagrams

### SVG Composition Flow

```
Slide
  ├─ title, content, type
  └─→ CompositionEngine.infer_layout()
        └─→ SVGComposer.compose(
              type="hero-background",
              theme=Theme,
              style_config=theme.visual_config
            )
              └─→ VisualStyleConfig heuristics applied
                  └─→ SVG primitives rendered (rect, circle, gradient, wave, grid)
                      └─→ <svg>...</svg> (W3C valid, ≤20 KB)
                          └─→ inline in HTML
```

### Image Enrichment Flow

```
EnrichContext (created for each slide)
  ├─ slide_index, prompt (inferred), seed
  └─→ EnrichEngine.enrich_all([contexts], providers=[...])
        ├─→ cache check: SHA256(prompt + provider) → .aio/cache/images/{hash}.jpg
        │     ├─ HIT: load cached image_bytes
        │     └─ MISS: try providers in order
        │
        ├─→ Provider 1: PollinationsProvider.generate(prompt)
        │     ├─ SUCCESS: image_bytes populated, provider_used="pollinations"
        │     └─ TIMEOUT/ERROR: try next provider
        │
        ├─→ Provider 2: OpenAIProvider.generate(prompt)
        │     ├─ SUCCESS: image_bytes populated, provider_used="openai"
        │     └─ TIMEOUT/ERROR: try next provider
        │
        ├─→ Provider 3: UnsplashProvider.generate(prompt)
        │     ├─ SUCCESS: image_bytes populated, provider_used="unsplash"
        │     └─ TIMEOUT/ERROR: try SVG fallback
        │
        └─→ SVG Fallback: SVGComposer.compose("feature-illustration", ...)
              ├─ is_placeholder=True
              ├─ provider_used="svg"
              └─ image_bytes=None (no JPEG)

Final: EnrichContext with image_bytes (JPEG or SVG), provider_used, is_placeholder
       └─→ base64_data_uri(image_bytes) if not placeholder
           └─→ inline in HTML <img src="data:image/jpeg;base64,...">
```

### Caching & Lifecycle Flow

```
First Build:
  ├─ enrich_all([contexts])
  └─→ Provider generates → image_bytes
      └─→ SHA256(prompt + provider) → hash
          └─→ cache_set(hash, image_bytes, CacheEntry(...))
              └─→ .aio/cache/images/{hash}.jpg written
                  └─→ .aio/meta.json updated with CacheEntry metadata

Second Build (same prompts):
  ├─ enrich_all([contexts])
  └─→ cache_get(hash) → image_bytes found
      └─→ 95% faster (no API calls)
          └─→ return cached EnrichContext

LRU Eviction (when .aio/cache/images/ > 100 MB):
  ├─ sort CacheEntry[] by timestamp (oldest first)
  └─→ delete oldest entries until size < 50 MB
```

---

## Key Design Decisions

1. **Deterministic SVG Generation**: `seed = hash(theme_id + composite_type)` ensures reproducibility across builds
2. **Multi-Provider Fallback Chain**: Graceful degradation from Pollinations → OpenAI → Unsplash → SVG
3. **Cache Keying**: `SHA256(prompt + provider_name)` ensures same prompt on different providers = different cache entries
4. **Offline-First**: Base64 data-URIs eliminate external dependencies (Article II)
5. **Lazy Validation**: SVG sanitization deferred to inline_assets step (prevent orphaned files on error)
6. **TDD-First Testing**: All entities have unit + integration tests before implementation

---
