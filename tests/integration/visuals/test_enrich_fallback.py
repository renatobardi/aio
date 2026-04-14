"""Integration tests for provider fallback chain."""

import pytest
from aio._enrich import EnrichEngine, EnrichContext


class TestFallbackChain:
    """Test multi-provider fallback chain."""

    def test_enrich_all_returns_contexts(self):
        """Test enrich_all returns enriched contexts."""
        contexts = [
            EnrichContext(slide_index=0, prompt="Test image", seed=123),
        ]
        result = EnrichEngine.enrich_all(contexts)
        assert len(result) == len(contexts)
        assert all(isinstance(c, EnrichContext) for c in result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
