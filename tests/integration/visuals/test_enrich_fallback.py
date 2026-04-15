"""Integration tests for provider fallback chain."""

from unittest.mock import patch

import pytest

from aio._enrich import EnrichContext, EnrichEngine


class TestFallbackChain:
    """Test multi-provider fallback chain."""

    def test_enrich_all_returns_contexts(self):
        """Test enrich_all returns enriched contexts."""
        # Mock urllib.request.urlopen to avoid real API calls
        def mock_urlopen(url, timeout=30):
            raise Exception("API unavailable in test")

        contexts = [
            EnrichContext(slide_index=0, prompt="Test image", seed=123),
        ]
        with patch("urllib.request.urlopen", side_effect=mock_urlopen):
            result = EnrichEngine.enrich_all(contexts)
        assert len(result) == len(contexts)
        assert all(isinstance(c, EnrichContext) for c in result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
