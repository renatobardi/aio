# Interface Contract: Image Generation API Engine

**Feature**: Phase 2.5 — Visual Richness  
**Created**: 2026-04-13  
**Location**: `src/aio/_enrich.py`

---

## EnrichEngine Interface

### Function: enrich_all()

**Signature**:
```python
def enrich_all(
    contexts: list[EnrichContext],
    providers: list[str] = ["pollinations", "openai", "unsplash"],
    timeout_per_image: int = 10,
    parallel_requests: int = 4
) -> list[EnrichContext]
```

**Purpose**: Enrich slides with images via multi-provider fallback chain with intelligent caching.

**Parameters**:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `contexts` | list[EnrichContext] | ✓ | — | Per-slide enrichment state with prompts |
| `providers` | list[str] | | ["pollinations", "openai", "unsplash"] | Provider names to try in order; "svg" is implicit final fallback |
| `timeout_per_image` | int | | 10 | Timeout seconds per image generation |
| `parallel_requests` | int | | 4 | Max concurrent API requests (rate limiting) |

**Returns**: `list[EnrichContext]` — Updated contexts with image_bytes (or is_placeholder=True)

**Throws**: None — Never raises; returns degraded state (SVG fallback) on all errors

**Behavior**:

1. **Cache Check**: For each context, compute `hash = SHA256(prompt + provider_name)`
   - If hash exists in `.aio/cache/images/`, load cached JPEG → context.image_bytes
   - Mark as from_cache=True in logs
2. **Provider Loop** (with timeout and retry logic):
   ```
   for provider in providers:
       for context in contexts (with parallelization):
           if context.image_bytes already populated:
               continue  # Skip if cache hit
           
           try:
               bytes = provider.generate(context.prompt, timeout=timeout_per_image)
               context.image_bytes = bytes
               context.provider_used = provider.name
               cache_set(context.prompt, provider.name, bytes)
               break  # Success; move to next context
           except TimeoutError:
               retry (up to 3x with exponential backoff: 2s, 4s, 8s)
           except Exception as e:
               log warning; continue to next provider
   ```
3. **SVG Fallback** (if all providers fail):
   - Call `SVGComposer.compose("feature-illustration", theme, ...)`
   - Set context.is_placeholder=True, context.provider_used="svg"
   - No image_bytes generated (SVG embedded separately)
4. **Return** updated contexts

**Performance**:
- 10-slide deck: ~15–30s with Pollinations (parallel 4), ~45–120s with OpenAI
- Cache hit: <100ms per image

**Example**:
```python
contexts = [
    EnrichContext(slide_index=0, prompt="Business growth chart"),
    EnrichContext(slide_index=1, prompt="Team collaboration"),
    ...
]

enriched = enrich_all(contexts, providers=["pollinations", "openai"])

for ctx in enriched:
    if ctx.image_bytes:
        print(f"Slide {ctx.slide_index}: {len(ctx.image_bytes)} bytes from {ctx.provider_used}")
    else:
        print(f"Slide {ctx.slide_index}: SVG fallback (placeholder={ctx.is_placeholder})")
```

---

## ImageProvider Interface

### Abstract Base

```python
@dataclass
class ImageProvider:
    api_key: str | None = None
    timeout_seconds: int = 10
    
    def check_api(self) -> bool:
        """Check if API is reachable and authenticated.
        
        Returns: True if ready; False if unavailable.
        """
        raise NotImplementedError
    
    def generate(
        self,
        prompt: str,
        width: int = 800,
        height: int = 450,
        seed: int | None = None
    ) -> bytes:
        """Generate image and return JPEG bytes.
        
        Args:
            prompt: Image description (~100 chars)
            width: Output width (pixels)
            height: Output height (pixels)
            seed: Deterministic seed (if supported)
        
        Returns: JPEG bytes (magic bytes: 0xFF 0xD8 0xFF)
        
        Raises:
            TimeoutError: API call exceeded timeout_seconds
            ValueError: Invalid prompt or parameters
            ConnectionError: Network/auth failure
            NotImplementedError: Feature not supported by provider
        """
        raise NotImplementedError
```

### PollinationsProvider

**URL**: `image.pollinations.ai?prompt={prompt}&width={width}&height={height}`

**Contract**:
```python
class PollinationsProvider(ImageProvider):
    api_key = None  # No key required
    timeout_seconds = 8
    
    def check_api(self) -> bool:
        """Always returns True (free API, always available)."""
        return True
    
    def generate(self, prompt: str, width: int = 800, height: int = 450,
                 seed: int | None = None) -> bytes:
        """Fetch image from Pollinations.ai.
        
        - Returns PNG; caller converts to JPEG
        - Deterministic if seed provided
        """
```

**Expected Response**:
- Status: 200 OK
- Content-Type: image/png
- Body: PNG bytes (magic: 0x89 0x50 0x4E 0x47)
- Time: <8s (P95)

**Fallback**: If timeout, raise TimeoutError

---

### OpenAIProvider

**Endpoint**: `POST https://api.openai.com/v1/images/generations`

**Contract**:
```python
class OpenAIProvider(ImageProvider):
    api_key: str = os.environ.get("OPENAI_API_KEY")
    timeout_seconds = 30
    model = "dall-e-3"
    
    def check_api(self) -> bool:
        """Verify OPENAI_API_KEY is set; optional: make test call."""
        return bool(self.api_key)
    
    def generate(self, prompt: str, width: int = 800, height: int = 450,
                 seed: int | None = None) -> bytes:
        """Call DALL-E 3 and return b64-decoded JPEG.
        
        - Requires OPENAI_API_KEY env var
        - Cost: ~$0.08 per 1024x1024, ~$0.12 per call (scaled)
        - Estimated cost shown to user before execution
        """
```

**Request**:
```json
{
  "model": "dall-e-3",
  "prompt": "Business growth chart with upward trend",
  "n": 1,
  "size": "1024x1024",
  "response_format": "b64_json"
}
```

**Response**:
```json
{
  "created": 1234567890,
  "data": [{
    "b64_json": "iVBORw0KG...",
    "revised_prompt": "..."
  }]
}
```

**Cost Estimation**:
- Input: (prompt length / 1000) × $0.02
- Image: 1 × $0.08 per 1024×1024
- Total: ~$0.08–0.15 per image
- Budget warning: Before generating N images, show "This will cost ~$X; continue? (Y/n)"

---

### UnsplashProvider

**Endpoint**: `GET https://api.unsplash.com/search/photos?query={prompt}&client_id={api_key}`

**Contract**:
```python
class UnsplashProvider(ImageProvider):
    api_key: str = os.environ.get("UNSPLASH_API_KEY")
    timeout_seconds = 8
    
    def check_api(self) -> bool:
        """Verify UNSPLASH_API_KEY is set."""
        return bool(self.api_key)
    
    def generate(self, prompt: str, width: int = 800, height: int = 450,
                 seed: int | None = None) -> bytes:
        """Search Unsplash photos and return first JPEG.
        
        - Retry 3x on 429 (rate limit)
        - Resize to width×height
        - Convert to JPEG
        """
```

**Request**:
```
GET /search/photos?query=business+growth+chart&client_id=...&per_page=1
```

**Response**:
```json
{
  "results": [{
    "urls": {
      "full": "https://images.unsplash.com/...",
      "regular": "https://images.unsplash.com/...?w=1080&q=80"
    }
  }]
}
```

**Retry Logic**: 429 → wait 2s → retry (3x total)

---

## Caching Interface

### Function: cache_get()

**Signature**:
```python
def cache_get(hash: str) -> bytes | None
```

**Returns**: JPEG bytes if cache hit; None if miss or invalid

---

### Function: cache_set()

**Signature**:
```python
def cache_set(hash: str, image_bytes: bytes, entry: CacheEntry) -> None
```

**Behavior**:
1. Write `.aio/cache/images/{hash}.jpg`
2. Update `.aio/meta.json` with CacheEntry metadata
3. Trigger LRU eviction if total size > 100 MB

---

## Fallback Strategy

**Sequence**:
```
Pollinations (free) → OpenAI (paid, opt-in) → Unsplash (free, opt-in) → SVG
```

**Conditions**:
1. **Pollinations**: Always available; try first
   - Timeout: 8s
   - If timeout → try next
2. **OpenAI**: Only if `--image-provider openai` AND `OPENAI_API_KEY` set
   - Timeout: 30s
   - If timeout → try next
3. **Unsplash**: Only if `--image-provider unsplash` AND `UNSPLASH_API_KEY` set
   - Timeout: 8s
   - If timeout or 404 (no results) → try next
4. **SVG**: Always available fallback
   - Timeout: <500ms
   - Never fails

**Error Logging**:
```
WARNING: Pollinations timeout (8.2s); trying OpenAI...
WARNING: OpenAI connection error; trying Unsplash...
WARNING: Unsplash rate limit; using SVG fallback for slides [2, 5, 8]
```

---

## Integration Points

### 1. Build Pipeline Integration
**File**: `src/aio/commands/build.py`  
**Step 4** (render_document):
```python
if args.enrich:
    enriched = enrich_all(
        contexts,
        providers=parse_providers_from_flags(args),
        timeout_per_image=10,
        parallel_requests=config.get("parallel_requests", 4)
    )
    # Update slide contexts with image_bytes or is_placeholder
```

### 2. CLI Flags Integration
**File**: `src/aio/commands/build.py`

```python
@app.command("build")
def build(
    ...
    enrich: bool = typer.Option(False, "--enrich", help="Enable image generation"),
    image_provider: str = typer.Option("pollinations", "--image-provider", 
                                       help="Provider: pollinations|openai|unsplash"),
    cache_clear: bool = typer.Option(False, "--cache-clear", help="Clear all caches"),
    cache_clear_images: bool = typer.Option(False, "--cache-clear-images", 
                                            help="Clear image cache only"),
    cache_stats: bool = typer.Option(False, "--cache-stats", help="Show cache stats"),
):
    pass
```

### 3. HTML Embedding Integration
**File**: `src/aio/composition/templates/base.j2`

```jinja2
{% if slide.image_bytes %}
  <img src="data:image/jpeg;base64,{{ slide.image_bytes | b64encode }}" 
       alt="Enriched slide image" />
{% elif slide.is_placeholder %}
  <div class="svg-placeholder">{{ slide.svg_composite | safe }}</div>
{% endif %}
```

---

## Success Criteria

| SC ID | Criterion | Test |
|-------|-----------|------|
| SC-410 | Pollinations <8s (P95) | `pytest tests/integration/visuals/test_pollinations_provider.py::test_response_time` |
| SC-411 | OpenAI <30s (P95), cost ≤$0.15 | Mock OPENAI response; verify cost calc |
| SC-412 | Cache hit 95% faster | Time uncached vs. cached; assert <100ms cached |
| SC-414 | SVG fallback <500ms | Timeout Pollinations; measure fallback time |
| SC-415 | 10-slide deck <45s (Pollinations), <120s (OpenAI) | Full pipeline test with timers |
| SC-416 | Data-URIs <3 MB (10-slide deck) | Sum base64 sizes; assert ≤3 MB |

---
