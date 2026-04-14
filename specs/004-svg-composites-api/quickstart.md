# Quickstart: SVG Composites & Image Generation API

## Overview

The SVG Composites Engine and Image Generation API add visual richness to AIO presentations through:
- **Deterministic SVG compositions** (8 types) matching theme palettes
- **Multi-provider image generation** (Pollinations, OpenAI, Unsplash) with intelligent fallback
- **Smart caching** with LRU eviction for rebuild performance
- **Theme integration** via DESIGN.md section 10 (Visual Style Preferences)

---

## 1. Using SVGComposer for Deterministic Composites

### Basic Usage

```python
from aio.visuals.svg.composites import SVGComposer, VisualStyleConfig
from aio.themes.loader import load_registry

# Load a theme from registry
registry = load_registry()
theme_record = next((t for t in registry if t.id == "linear"), None)

# Prepare theme dict for SVGComposer
theme = {
    "id": theme_record.id,
    "palette": theme_record.colors,
    "visual_config": theme_record.metadata.get("visual_config", {})
}

# Generate hero-background SVG
svg = SVGComposer.compose(
    composite_type="hero-background",
    theme=theme,
    dimensions=(1920, 1080),
    seed=12345
)
print(svg)  # <svg xmlns="..." viewBox="0 0 1920 1080">...</svg>
```

### Supported Composition Types

| Type | Use Case |
|------|----------|
| `hero-background` | Title slides, cover pages |
| `feature-illustration` | Product features, side-by-side comparisons |
| `stat-decoration` | Statistics, metrics, key numbers |
| `section-divider` | Visual breaks between sections |
| `abstract-art` | Creative backgrounds, transitional slides |
| `process-steps` | Workflows, numbered sequences |
| `comparison-split` | Before/after, two options |
| `grid-showcase` | Portfolio, gallery, grid layouts |

### Visual Style Preferences

The DESIGN.md section 10 controls SVG composition styling:

```yaml
# DESIGN.md section 10
Visual Style Preference: tech
Pattern: geometric
Curvature: sharp
Animation Preference: static
```

**Heuristics Applied**:
- **tech** → straight lines, grid patterns, sharp angles
- **organic** → curves, waves, soft edges
- **minimal** → sparse elements, high contrast
- **geometric** → structured shapes, symmetrical

---

## 2. Image Generation with Multi-Provider Fallback

### Setup

```python
from aio._enrich import EnrichEngine, EnrichContext
from aio.themes.loader import load_registry

# Create enrichment contexts (one per slide)
contexts = [
    EnrichContext(
        slide_index=0,
        prompt="Modern business team collaborating in office",
        seed=hash("my-deck:0") % (2**31)
    ),
    EnrichContext(
        slide_index=1,
        prompt="Growth chart with upward trend line",
        seed=hash("my-deck:1") % (2**31)
    ),
]

# Enrich with images (Pollinations → OpenAI → Unsplash → SVG fallback)
enriched = EnrichEngine.enrich_all(
    contexts,
    providers=["pollinations", "openai", "unsplash"],
    timeout_per_image=10,
    parallel_requests=4
)

for ctx in enriched:
    print(f"Slide {ctx.slide_index}: {ctx.provider_used} ({ctx.is_placeholder=})")
    if ctx.image_bytes:
        print(f"  Image size: {len(ctx.image_bytes) / 1024:.1f} KB")
```

### Provider Behavior

| Provider | Cost | Setup | Speed |
|----------|------|-------|-------|
| **Pollinations** | Free | None | ~5-8s |
| **OpenAI DALL-E** | ~$0.08–0.12/image | `OPENAI_API_KEY` env var | ~20-30s |
| **Unsplash** | Free | `UNSPLASH_API_KEY` env var | ~3-5s |
| **SVG Fallback** | Free | Auto | <500ms |

---

## 3. Cache Management

### Automatic Caching

Cache is automatic via `cache_init()` called at build start:

```bash
# Build with automatic caching
aio build slides.md --enrich
# First build: ~30s (images generated and cached)
# Second build: ~2s (cache hits on all images)
```

### Manual Cache Operations

```bash
# Show cache stats
aio build slides.md --cache-stats
# Output:
# Cache statistics:
#   Entries: 8
#   Size: 12.3 MB / 100.0 MB
#   AIO version: 0.1.0

# Clear all caches
aio build slides.md --cache-clear

# Clear image cache only
aio build slides.md --cache-clear-images
```

### Cache Internals

```python
from aio._enrich import cache_get_stats, cache_invalidate, cache_init

# Get current stats
stats = cache_get_stats()
print(f"Cache size: {stats['total_size_mb']} MB")

# Manually clear cache
cache_invalidate()

# Reinitialize with new version
cache_init(aio_version="0.2.0")
```

---

## 4. Theme Integration (Section 10)

### Extracting Visual Config from DESIGN.md

```python
from aio.themes.loader import load_registry
from aio.themes.parser import extract_visual_style_config, parse_design_md

# Load theme
registry = load_registry()
theme = next((t for t in registry if t.id == "linear"), None)

# Visual config automatically extracted during load
visual_config = theme.metadata.get("visual_config", {})
print(visual_config)
# Output: {'visual_style_preference': 'tech', 'pattern': 'geometric', ...}
```

### Creating/Updating DESIGN.md Section 10

```markdown
## 10. Visual Style Preference

```yaml
visual_style_preference: tech
pattern: grid
curvature: sharp
animation_preference: static
```

- Defines automatic SVG composition styling for this theme
- Applies to all 8 composition types (hero, feature, stat, etc.)
- Overrides defaults (tech/geometric/sharp/static) when present
```

### Validating Themes

```bash
# Validate theme has complete section 10
aio theme validate linear

# Create new theme from existing with section 10
aio theme create my-theme --from linear

# Edit theme DESIGN.md
aio theme create my-theme --edit
```

---

## 5. Integration in Build Pipeline

### Full Example: Building Rich Presentation

```python
from pathlib import Path
from aio.commands.build import build_pipeline

# Build with all features enabled
result = build_pipeline(
    input_path=Path("slides.md"),
    output=Path("build/slides.html"),
    theme_id="linear",
    enrich=True,
    serve_mode=False
)

print(f"Built {result.slide_count} slides in {result.elapsed_seconds:.1f}s")
print(f"Output: {result.output_path} ({result.byte_size / 1024:.1f} KB)")
print(f"Enrichment used: {result.enrich_used}")
```

---

## 6. Debugging & Troubleshooting

### Enable Verbose Logging

```bash
aio build slides.md --enrich -v
# Debug output shows:
# Cache HIT/MISS, provider selection, SVG rendering, etc.
```

### Check Theme Compliance

```bash
# Validate all aspects of a theme
aio theme validate linear --css

# Shows section 10 status, CSS validity, WCAG contrast ratios
```

### Performance Profiling

```bash
# Time individual composition types
from aio.visuals.svg.composites import SVGComposer
import time

for composite_type in SVGComposer.SUPPORTED_TYPES:
    start = time.perf_counter()
    svg = SVGComposer.compose(composite_type, theme)
    elapsed = time.perf_counter() - start
    print(f"{composite_type}: {elapsed*1000:.1f}ms")
```

---

## 7. API Reference

### SVGComposer

```python
class SVGComposer:
    @staticmethod
    def compose(
        composite_type: str,          # One of 8 types
        theme: dict,                  # {id, palette, visual_config}
        dimensions: tuple = (1920, 1080),
        seed: int | None = None       # Deterministic seed
    ) -> str:  # Valid W3C SVG string
        """Generate deterministic SVG composition."""
```

### EnrichEngine

```python
class EnrichEngine:
    @staticmethod
    def enrich_all(
        contexts: list[EnrichContext],
        providers: list[str] | None = None,
        timeout_per_image: int = 10,
        parallel_requests: int = 4
    ) -> list[EnrichContext]:
        """Enrich slides with images (cache-first, multi-provider fallback)."""
```

### Cache Functions

```python
cache_get(hash_key: str) -> bytes | None
    # Retrieve from cache; None if not found or version mismatch

cache_set(hash_key: str, image_bytes: bytes, entry: CacheEntry) -> None
    # Store in cache; auto-evicts oldest entries if > 100 MB

cache_invalidate() -> None
    # Clear all cache entries

cache_get_stats() -> dict
    # {entry_count, total_size_mb, max_size_mb, aio_version}

cache_init(aio_version: str) -> None
    # Initialize cache, detect version mismatches, clear on change
```

---

## Next Steps

- **Read the contract specs**: `contracts/svg-composites.md` and `contracts/image-generation.md`
- **Check integration tests**: `tests/integration/visuals/` and `tests/integration/themes/`
- **Explore CLI**: `aio build --help`, `aio theme --help`
- **Report issues**: GitHub issues with logs from `aio build -v`
