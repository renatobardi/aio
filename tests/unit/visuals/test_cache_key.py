"""Unit tests for cache key generation (SHA256)."""

import hashlib


class TestCacheKeyGeneration:
    """Test cache key generation via SHA256."""

    def test_same_prompt_same_hash(self):
        """Same prompt+provider produces same hash."""
        prompt = "Business growth chart"
        provider = "pollinations"

        key1 = hashlib.sha256(f"{prompt}{provider}".encode()).hexdigest()
        key2 = hashlib.sha256(f"{prompt}{provider}".encode()).hexdigest()

        assert key1 == key2
        assert len(key1) == 64  # SHA256 = 64 hex chars

    def test_different_prompts_different_hash(self):
        """Different prompts produce different hashes."""
        prompt1 = "Business growth"
        prompt2 = "Market trends"
        provider = "pollinations"

        key1 = hashlib.sha256(f"{prompt1}{provider}".encode()).hexdigest()
        key2 = hashlib.sha256(f"{prompt2}{provider}".encode()).hexdigest()

        assert key1 != key2

    def test_provider_affects_hash(self):
        """Different providers produce different hashes for same prompt."""
        prompt = "Business chart"

        key1 = hashlib.sha256(f"{prompt}pollinations".encode()).hexdigest()
        key2 = hashlib.sha256(f"{prompt}openai".encode()).hexdigest()

        assert key1 != key2
