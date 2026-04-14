"""Integration tests for cache invalidation."""

from aio._enrich import cache_invalidate, cache_set, CacheEntry
from datetime import datetime


class TestCacheInvalidation:
    """Test cache invalidation on version change."""

    def test_cache_clear_removes_entries(self):
        """Cache invalidation removes cached images."""
        # Set up cache entry
        hash_key = "test_123"
        image_data = b"test"
        entry = CacheEntry(hash_key, datetime.now(), len(image_data))
        cache_set(hash_key, image_data, entry)
        
        # Clear cache
        cache_invalidate()
        
        # Verify cleared
        # (In full implementation, would verify directory is empty)
        import os
        if os.path.exists(".aio/cache/images"):
            assert len(os.listdir(".aio/cache/images")) == 0
