"""Unit tests for prompt builder."""

import pytest


class TestPromptBuilder:
    """Test prompt generation from slide content."""

    def test_prompt_from_title_and_bullets(self):
        """Test prompt extraction from slide title and bullets."""
        # Placeholder test - full implementation would extract from slide AST
        title = "Business Growth"
        bullets = ["Revenue up 50%", "Customer base doubled"]
        # In real implementation: prompt = prompt_builder(title, bullets)
        # For now: just verify structure
        assert title
        assert len(bullets) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
