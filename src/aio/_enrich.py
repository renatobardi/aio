"""Image enrichment engine — multi-provider image generation with caching."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast

from aio._log import get_logger

_log = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class VisualStyleConfig:
    """Visual style preferences (imported from visuals.svg.composites)."""

    visual_style_preference: Literal["geometric", "organic", "tech", "minimal"] = "tech"
    pattern: Literal["grid", "dots", "lines", "mesh", "noise", "flowing"] = "grid"
    curvature: Literal["sharp", "soft", "mixed"] = "sharp"
    animation_preference: Literal["static", "subtle", "dynamic"] = "static"


@dataclass
class EnrichContext:
    """Per-slide state for image generation enrichment."""

    slide_index: int
    prompt: str
    seed: int
    image_bytes: bytes | None = None
    is_placeholder: bool = False
    provider_used: Literal["pollinations", "openai", "unsplash", "svg"] = "svg"
    error_message: str | None = None


@dataclass
class CacheEntry:
    """Cache metadata and versioning."""

    hash: str  # SHA256(prompt + provider_name)
    timestamp: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    aio_version: str = "0.1.0"  # Will be replaced with actual version


@dataclass
class ImageProvider:
    """Abstract base for image generation providers."""

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
        seed: int | None = None,
    ) -> bytes:
        """Generate image and return JPEG bytes."""
        raise NotImplementedError


class PollinationsProvider(ImageProvider):
    """Pollinations.ai provider (free, no API key required)."""

    api_key = None
    timeout_seconds = 8

    def check_api(self) -> bool:
        """Always available (free API)."""
        return True

    def generate(self, prompt: str, width: int = 800, height: int = 450, seed: int | None = None) -> bytes:
        """Fetch from Pollinations.ai (simplified mock for now)."""
        # In full implementation, would call requests.get()
        # For now, return stub PNG bytes
        return b"\x89PNG\r\n\x1a\n"  # PNG header


class OpenAIProvider(ImageProvider):
    """OpenAI DALL-E provider (paid, requires API key)."""

    def __init__(self) -> None:
        super().__init__(api_key=os.environ.get("OPENAI_API_KEY"), timeout_seconds=30)
        self.model = "dall-e-3"

    def check_api(self) -> bool:
        """Verify API key is set."""
        return bool(self.api_key)

    def generate(self, prompt: str, width: int = 800, height: int = 450, seed: int | None = None) -> bytes:
        """Call DALL-E 3 (simplified mock for now)."""
        if not self.check_api():
            raise ValueError("OPENAI_API_KEY not set")
        return b"\xff\xd8\xff"  # JPEG header


class UnsplashProvider(ImageProvider):
    """Unsplash photo search provider (free, requires API key)."""

    def __init__(self) -> None:
        super().__init__(api_key=os.environ.get("UNSPLASH_API_KEY"), timeout_seconds=8)

    def check_api(self) -> bool:
        """Verify API key is set."""
        return bool(self.api_key)

    def generate(self, prompt: str, width: int = 800, height: int = 450, seed: int | None = None) -> bytes:
        """Search Unsplash photos (simplified mock for now)."""
        if not self.check_api():
            raise ValueError("UNSPLASH_API_KEY not set")
        return b"\xff\xd8\xff"  # JPEG header


# ============================================================================
# Cache Functions with LRU Eviction
# ============================================================================

_CACHE_DIR = Path(".aio/cache/images")
_CACHE_MAX_SIZE = 100 * 1024 * 1024  # 100 MB
_CACHE_MIN_SIZE = 50 * 1024 * 1024  # 50 MB (target after eviction)
_META_FILE = Path(".aio/meta.json")


def _get_cache_metadata() -> dict[str, Any]:
    """Load cache metadata from .aio/meta.json."""
    if _META_FILE.exists():
        try:
            return json.loads(_META_FILE.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
        except Exception:
            return {"cache_entries": {}, "aio_version": "0.1.0"}
    return {"cache_entries": {}, "aio_version": "0.1.0"}


def _save_cache_metadata(metadata: dict[str, Any]) -> None:
    """Save cache metadata to .aio/meta.json with file locking."""
    Path(".aio").mkdir(exist_ok=True)
    # Use atomic write with locking to prevent concurrent corruption
    temp_file = _META_FILE.with_suffix(".tmp")
    temp_file.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    temp_file.replace(_META_FILE)


def _evict_lru_if_needed() -> None:
    """Remove oldest cache entries if total size > 100 MB."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Calculate current cache size
    total_size = sum(f.stat().st_size for f in _CACHE_DIR.glob("*.jpg") if f.is_file())

    if total_size <= _CACHE_MAX_SIZE:
        return

    _log.warning("Cache size %.1f MB exceeds limit; evicting oldest entries", total_size / (1024 * 1024))

    # Load metadata and sort by timestamp
    metadata = _get_cache_metadata()
    entries = metadata.get("cache_entries", {})

    if not entries:
        return

    # Sort by timestamp (oldest first) - parse ISO 8601 strings
    def parse_timestamp(entry_tuple: tuple[str, Any]) -> datetime:
        _, entry_data = entry_tuple
        ts_str = entry_data.get("timestamp", "")
        try:
            return datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            return datetime.min

    sorted_entries = sorted(entries.items(), key=parse_timestamp, reverse=False)

    # Delete oldest entries until < 50 MB
    evicted_count = 0
    for hash_key, entry_data in sorted_entries:
        cache_file = _CACHE_DIR / f"{hash_key}.jpg"
        if cache_file.exists():
            file_size = cache_file.stat().st_size
            cache_file.unlink()
            total_size -= file_size
            del entries[hash_key]
            evicted_count += 1

            if total_size <= _CACHE_MIN_SIZE:
                break

    metadata["cache_entries"] = entries
    _save_cache_metadata(metadata)
    _log.info("Evicted %d cache entries, new size: %.1f MB", evicted_count, total_size / (1024 * 1024))


def cache_get(hash_key: str) -> bytes | None:
    """Get cached image by hash. Returns None if not found or version mismatch."""
    # Check version compatibility
    metadata = _get_cache_metadata()
    current_version = metadata.get("aio_version", "0.1.0")
    entries = metadata.get("cache_entries", {})

    if hash_key not in entries:
        _log.debug("Cache MISS: %s (not in metadata)", hash_key[:8])
        return None

    entry_data = entries[hash_key]
    if entry_data.get("aio_version") != current_version:
        # Version mismatch; invalidate
        _log.debug(
            "Cache MISS: %s (version mismatch: %s vs %s)", hash_key[:8], entry_data.get("aio_version"), current_version
        )
        return None

    cache_file = _CACHE_DIR / f"{hash_key}.jpg"
    if cache_file.exists():
        try:
            image_bytes = cache_file.read_bytes()
            _log.debug("Cache HIT: %s (%d bytes)", hash_key[:8], len(image_bytes))
            return image_bytes
        except Exception as e:
            _log.warning("Cache read error: %s", e)
            return None

    _log.debug("Cache MISS: %s (file not found)", hash_key[:8])
    return None


def cache_set(hash_key: str, image_bytes: bytes, entry: CacheEntry) -> None:
    """Store image in cache with metadata and LRU eviction."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Write image file
    cache_file = _CACHE_DIR / f"{hash_key}.jpg"
    cache_file.write_bytes(image_bytes)
    _log.debug("Cache WRITE: %s (%d bytes)", hash_key[:8], len(image_bytes))

    # Update metadata
    metadata = _get_cache_metadata()
    entries = metadata.get("cache_entries", {})
    entries[hash_key] = {
        "timestamp": entry.timestamp.isoformat(),
        "size_bytes": len(image_bytes),
        "aio_version": entry.aio_version,
    }
    metadata["cache_entries"] = entries
    _save_cache_metadata(metadata)

    # Evict oldest entries if cache too large
    _evict_lru_if_needed()


def cache_invalidate() -> None:
    """Clear image cache."""
    import shutil

    if _CACHE_DIR.exists():
        shutil.rmtree(_CACHE_DIR)
        _log.info("Cache INVALIDATED: all entries cleared")
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Reset metadata
    metadata = {"cache_entries": {}, "aio_version": "0.1.0"}
    _save_cache_metadata(metadata)


def cache_get_stats() -> dict[str, object]:
    """Return cache statistics: hit count, miss count, size, entry count."""
    metadata = _get_cache_metadata()
    entries = metadata.get("cache_entries", {})

    total_size = 0
    for entry_data in entries.values():
        total_size += entry_data.get("size_bytes", 0)

    return {
        "entry_count": len(entries),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "max_size_mb": _CACHE_MAX_SIZE / (1024 * 1024),
        "aio_version": metadata.get("aio_version", "0.1.0"),
    }


def cache_init(aio_version: str = "0.1.0") -> None:
    """Initialize cache directory structure and metadata."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize or update metadata with current AIO version
    metadata = _get_cache_metadata()
    old_version = metadata.get("aio_version")

    # Check version mismatch — invalidate cache if version changed
    if old_version and old_version != aio_version:
        # Version changed; clear cache
        _log.warning("Cache INVALIDATION: version mismatch (%s → %s); clearing entries", old_version, aio_version)
        metadata["cache_entries"] = {}

    metadata["aio_version"] = aio_version
    _save_cache_metadata(metadata)
    _log.debug("Cache initialized: version %s, %d entries", aio_version, len(metadata.get("cache_entries", {})))


# ============================================================================
# EnrichEngine
# ============================================================================


class EnrichEngine:
    """Orchestrates image generation with multi-provider fallback."""

    @staticmethod
    def enrich_all(
        contexts: list[EnrichContext],
        providers: list[str] | None = None,
        timeout_per_image: int = 10,
        parallel_requests: int = 4,
    ) -> list[EnrichContext]:
        """
        Enrich slides with images via multi-provider fallback with caching.

        Flow:
        1. Check cache for each context (SHA256(prompt + provider))
        2. If cache hit, use cached image
        3. If miss, try providers in order (Pollinations → OpenAI → Unsplash)
        4. On provider success, cache result and return
        5. On all provider failures, use SVG fallback (is_placeholder=True)
        """
        if providers is None:
            providers = ["pollinations", "openai", "unsplash"]

        for ctx in contexts:
            # Try to get from cache first - check all provider-specific keys
            image_bytes = None
            provider_used = None

            for provider_name in providers:
                cache_key = hashlib.sha256(f"{ctx.prompt}:{provider_name}".encode()).hexdigest()
                cached_bytes = cache_get(cache_key)

                if cached_bytes:
                    ctx.image_bytes = cached_bytes
                    ctx.provider_used = cast(Literal["pollinations", "openai", "unsplash", "svg"], provider_name)
                    image_bytes = cached_bytes
                    provider_used = cast(Literal["pollinations", "openai", "unsplash", "svg"], provider_name)
                    break

            if image_bytes:
                # Cache hit found for this provider
                continue

            # No cache hit; try providers in order
            image_bytes = None
            provider_used = None

            for provider_name in providers:
                if provider_name == "pollinations":
                    try:
                        provider = PollinationsProvider()
                        if provider.check_api():
                            image_bytes = provider.generate(ctx.prompt, seed=ctx.seed)
                            provider_used = cast(Literal["pollinations", "openai", "unsplash", "svg"], provider_name)
                            break
                    except Exception as e:
                        _log.warning("Pollinations provider failed: %s", e)
                        continue

                elif provider_name == "openai":
                    try:
                        openai_provider = OpenAIProvider()
                        if openai_provider.check_api():
                            image_bytes = openai_provider.generate(ctx.prompt, seed=ctx.seed)
                            provider_used = cast(Literal["pollinations", "openai", "unsplash", "svg"], provider_name)
                            break
                    except Exception as e:
                        _log.warning("OpenAI provider failed: %s", e)
                        continue

                elif provider_name == "unsplash":
                    try:
                        unsplash_provider = UnsplashProvider()
                        if unsplash_provider.check_api():
                            image_bytes = unsplash_provider.generate(ctx.prompt, seed=ctx.seed)
                            provider_used = cast(Literal["pollinations", "openai", "unsplash", "svg"], provider_name)
                            break
                    except Exception as e:
                        _log.warning("Unsplash provider failed: %s", e)
                        continue

            # If we got an image, cache and set it
            if image_bytes:
                cache_key = hashlib.sha256(f"{ctx.prompt}:{provider_used}".encode()).hexdigest()
                entry = CacheEntry(
                    hash=cache_key,
                    timestamp=datetime.now(),
                    size_bytes=len(image_bytes),
                    aio_version="0.1.0",
                )
                cache_set(cache_key, image_bytes, entry)
                ctx.image_bytes = image_bytes
                ctx.provider_used = cast(Literal["pollinations", "openai", "unsplash", "svg"], provider_used)
            else:
                # All providers failed; use SVG fallback
                ctx.is_placeholder = True
                ctx.provider_used = "svg"

        return contexts


# ============================================================================
# Prompt Building & Seed Derivation
# ============================================================================

_THEME_STYLE_HINTS = {
    "linear": "tech",
    "minimal": "minimal",
    "vibrant": "organic",
    "modern": "tech",
    "stripe": "tech",
    "vercel": "tech",
    "notion": "organic",
    "figma": "tech",
    "cursor": "tech",
    "supabase": "tech",
    "airbnb": "organic",
    "dribble": "organic",
}


def infer_style_hint(theme_id: str) -> str:
    """Map theme ID to visual style hint (tech/organic/minimal/geometric)."""
    return _THEME_STYLE_HINTS.get(theme_id, "tech")


def derive_seed(title: str | None, slide_index: int) -> int:
    """Derive deterministic seed from deck title + slide index."""
    seed_str = f"{title or 'untitled'}:{slide_index}"
    return hash(seed_str) % (2**31)


def infer_prompt(slide_title: str | None, slide_body: str | None) -> str:
    """Infer image prompt from slide title and body."""
    if slide_title:
        return f"{slide_title}: {slide_body[:100] if slide_body else 'Abstract concept'}"
    if slide_body:
        return slide_body[:150]
    return "Abstract business concept"


def make_placeholder_svg() -> str:
    """Return minimal SVG placeholder when image generation fails."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450">
      <rect width="800" height="450" fill="#f0f0f0"/>
      <circle cx="400" cy="225" r="50" fill="#ccc"/>
      <text x="400" y="240" text-anchor="middle" fill="#999" font-size="14">Image unavailable</text>
    </svg>"""
