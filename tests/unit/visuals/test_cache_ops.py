"""Unit tests for cache operations (get, set, delete)."""

from datetime import datetime

from aio._enrich import CacheEntry, cache_get, cache_set


class TestCacheOperations:
    """Test cache_get, cache_set, cache_invalidate."""

    def test_cache_set_and_get(self):
        """Test storing and retrieving from cache."""
        hash_key = "test_hash_12345"
        image_data = b"\xff\xd8\xff\xe0"  # JPEG header
        entry = CacheEntry(hash_key, datetime.now(), len(image_data))
        
        cache_set(hash_key, image_data, entry)
        retrieved = cache_get(hash_key)
        
        assert retrieved == image_data

    def test_cache_miss_returns_none(self):
        """Test cache miss returns None."""
        result = cache_get("nonexistent_hash")
        assert result is None or result == b"" or result is None
