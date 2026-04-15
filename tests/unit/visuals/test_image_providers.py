"""Unit tests for image providers."""

import pytest

from aio._enrich import OpenAIProvider, PollinationsProvider, UnsplashProvider


class TestProviders:
    """Test image provider implementations."""

    def test_pollinations_check_api(self):
        """Test Pollinations always available."""
        provider = PollinationsProvider()
        assert provider.check_api() is True

    def test_openai_check_api_without_key(self):
        """Test OpenAI check returns False without API key."""
        import os

        # Temporarily remove API key
        old_key = os.environ.get("OPENAI_API_KEY")
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        provider = OpenAIProvider()
        assert provider.check_api() is False

        # Restore
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key

    def test_unsplash_check_api_without_key(self):
        """Test Unsplash check returns False without API key."""
        import os

        old_key = os.environ.get("UNSPLASH_API_KEY")
        if "UNSPLASH_API_KEY" in os.environ:
            del os.environ["UNSPLASH_API_KEY"]

        provider = UnsplashProvider()
        assert provider.check_api() is False

        if old_key:
            os.environ["UNSPLASH_API_KEY"] = old_key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
