# Image Generation Troubleshooting Guide

## Overview

This guide helps diagnose and resolve issues with image generation, caching, and provider fallback in AIO.

---

## Common Issues

### 1. "Image API Timeout" / Slow Builds

**Symptom**: Build takes 30+ seconds with `--enrich` flag.

**Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| Network latency to Pollinations | Use `--image-provider openai` if OPENAI_API_KEY set; try again later |
| Pollinations.ai down | Check https://status.pollinations.ai; use OpenAI as fallback |
| Too many parallel requests | Reduce `--parallel-requests` (default 4): `aio build --parallel-requests 2` |
| Local network issues | Check internet connection; verify DNS resolution |

**Debug**:
```bash
aio build slides.md --enrich -v 2>&1 | grep -i "timeout\|error\|warning"
```

---

### 2. Cache Not Working / Rebuild Still Slow

**Symptom**: Second build with `--enrich` still takes 20+ seconds; cache stats show entries but they're not used.

**Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| Cache entries expired (version mismatch) | Check AIO version: `aio build --cache-stats`; clear if mismatch detected |
| Different prompts each build | Verify slide content hasn't changed; check `aio build -v` logs for prompt hashes |
| Cache file corrupted | Clear cache: `aio build --cache-clear` and rebuild |
| .aio/meta.json corrupted | Delete `.aio/meta.json` and rebuild to reinitialize |

**Debug**:
```bash
# Check cache state
aio build slides.md --cache-stats

# Show detailed cache operations
aio build slides.md --enrich -v 2>&1 | grep "Cache HIT\|Cache MISS\|Cache WRITE"

# Clear and rebuild
aio build slides.md --cache-clear --enrich
```

---

### 3. "All Providers Failed" / SVG Fallback Used

**Symptom**: Build completes but all slides get SVG placeholders instead of generated images.

**Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| Pollinations.ai is down | Wait for service recovery; monitor https://status.pollinations.ai |
| OpenAI API key invalid | Verify: `echo $OPENAI_API_KEY` and test with OpenAI website |
| Unsplash API key invalid | Verify key at https://unsplash.com/oauth/applications |
| Network blocked / firewall | Check if outbound HTTPS to pollinations.ai, api.openai.com, or api.unsplash.com is blocked |
| No providers specified in flags | Ensure `--image-provider` is set; default is "pollinations" |

**Debug**:
```bash
# Force specific provider; see which fails
aio build slides.md --enrich --image-provider openai -v 2>&1 | tail -20

# Check environment variables
env | grep -i "api_key\|openai\|unsplash"

# Verify network connectivity
curl -I https://image.pollinations.ai
curl -I https://api.openai.com
curl -I https://api.unsplash.com
```

---

### 4. "JPEG Conversion Failed" / Invalid Image Bytes

**Symptom**: Build logs show provider returned data, but image is not embedded in HTML.

**Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| Provider returned non-JPEG data (PNG/WebP) | Expected; conversion to JPEG happens automatically in `EnrichEngine` |
| Image file corrupted | Retry build with `--cache-clear` to regenerate |
| Pillow (PIL) not installed | Install: `pip install -e ".[enrich]"` (includes pillow) |

**Debug**:
```bash
# Verify enrich extras installed
pip show pillow

# Check image bytes in logs
aio build slides.md --enrich -v 2>&1 | grep "image_bytes\|JPEG"
```

---

### 5. "Cost Warning" / OpenAI Budget Concerns

**Symptom**: OpenAI cost estimation shown before build; concerned about expenses.

**Solutions**:

1. **Use Pollinations (free) instead**: Default provider; costs $0
2. **Limit slides**: Enrich only key slides with prompts; others get SVG
3. **Use Unsplash (free)**: `--image-provider unsplash` if you have API key
4. **Review cost**:
   - OpenAI DALL-E 3: ~$0.08 per image
   - 10-slide deck: ~$0.80 total
   - Cost warning shown before execution; answer "N" to skip

**Debug**:
```bash
# See cost estimate without generating
aio build slides.md --enrich --image-provider openai --dry-run

# Use free provider
aio build slides.md --enrich  # Pollinations by default (free)
```

---

### 6. SVG Fallback Not Rendering / Invalid SVG

**Symptom**: SVG fallback shown in HTML but appears blank or broken in browser.

**Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| SVG contains `<script>` tags (security violation) | SVGComposer sanitizes automatically; rare edge case |
| SVG viewBox mismatch | Check theme config; report issue with theme ID |
| Browser doesn't support embedded SVG | Use modern browser (Chrome, Firefox, Safari); IE11 not supported |

**Debug**:
```bash
# Extract SVG from HTML and validate
grep -o '<svg[^>]*>.*</svg>' build/slides.html | head -1 | xmllint --noout -  2>&1

# Force SVG fallback to test
aio build slides.md --enrich --image-provider fake  # All slides get SVG
```

---

## Performance Issues

### Build Takes Too Long

**Profile**:
```bash
# Time each step with verbose logging
time aio build slides.md --enrich -v

# Expected times:
# - Parse: <100ms
# - Analyze/Compose: <500ms
# - Render: <200ms
# - Enrich (first build): 15-30s (image generation)
# - Enrich (cached): <2s
# - Inline: <100ms
```

**Optimization**:
```bash
# Reduce parallelism if network-bound
aio build slides.md --enrich --parallel-requests 2

# Skip enrichment for drafts
aio build slides.md  # No --enrich; fast

# Reuse cache across builds
aio build slides.md --enrich  # Populate cache
aio build slides.md --enrich  # Cache hit; ~2s

# Profile SVG composition (should be <50ms per slide)
python -c "
from aio.visuals.svg.composites import SVGComposer
from aio.themes.loader import load_registry
import time
theme = {
    'id': 'linear',
    'palette': {'primary': '#0EA5E9', 'secondary': '#06B6D4'},
    'visual_config': {}
}
start = time.perf_counter()
svg = SVGComposer.compose('hero-background', theme)
print(f'SVG generation: {(time.perf_counter() - start)*1000:.1f}ms')
"
```

---

## Cache Issues

### Cache Growing Too Large

**Symptom**: `.aio/cache/images/` > 100 MB; slowdown when LRU eviction triggers.

**Solution**:
```bash
# Check current size
aio build slides.md --cache-stats

# Clear to start fresh
aio build slides.md --cache-clear

# Future: configure max size (currently hardcoded to 100 MB)
```

### Cache Invalidated Unexpectedly

**Symptom**: Cache stats show 0 entries after update; rebuild generates all images again.

**Cause**: AIO version changed (expected behavior for breaking changes)

**Solution**:
```bash
# Check version
aio --version

# Cache is version-locked to current AIO version
# If version changed, cache is automatically cleared for safety
```

---

## Provider-Specific Issues

### Pollinations: Slow or Timeout

```bash
# Reduce timeout if Pollinations is flaky
# (Currently hardcoded to 8s; fallback to OpenAI)

aio build slides.md --enrich --image-provider openai
```

### OpenAI: "Invalid API Key"

```bash
# Verify key is set and valid
echo $OPENAI_API_KEY

# Test directly with curl
curl https://api.openai.com/v1/images/generations \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"dall-e-3","prompt":"test","n":1,"size":"1024x1024"}'
```

### Unsplash: "Rate Limited" (429 error)

```bash
# Unsplash free tier: 50 requests/hour
# Solution: Wait or upgrade to paid tier
# Or use Pollinations (no rate limit)

aio build slides.md --enrich  # Pollinations; no rate limit
```

---

## Reporting Issues

### Gather Debug Info

```bash
# Capture full build log
aio build slides.md --enrich -v 2>&1 | tee build.log

# Check environment
env | grep -i "aio\|openai\|unsplash\|pollinations" > env.log

# Check cache state
aio build slides.md --cache-stats > cache.log

# Check theme compliance
aio theme validate linear --css > theme.log

# Bundle for support
tar czf debug.tar.gz build.log env.log cache.log theme.log slides.md
```

### Open GitHub Issue

Include in issue:
1. **Error message** (full output from `aio build -v`)
2. **AIO version** (`aio --version`)
3. **Environment** (Python version, OS, pip packages)
4. **Reproducible steps** (minimal slides.md example)
5. **Provider used** (`--image-provider pollinations | openai | unsplash`)
6. **Cache state** (output of `aio build --cache-stats`)

---

## Prevention

### Best Practices

1. **Pin provider at build time**: `--image-provider pollinations` (explicit, not default-dependent)
2. **Monitor cache size**: Run `aio build --cache-stats` periodically
3. **Test early**: Build with `--enrich` on small deck first; verify images
4. **Use dry-run for cost estimates**: `aio build --dry-run --image-provider openai`
5. **Enable logging**: Always use `-v` for troubleshooting; save logs
6. **Keep AIO updated**: Cache is version-locked; update AIO to reset cache safely

---

## Support

- **GitHub Issues**: https://github.com/renatobardi/aio/issues
- **Documentation**: `specs/004-svg-composites-api/quickstart.md`
- **Code**: `src/aio/_enrich.py`, `src/aio/visuals/svg/composites.py`
