"""Integration tests for SVG fallback behavior."""

import pytest

from aio.visuals.svg.composites import SVGComposer


class TestSVGFallback:
    """Test SVG fallback on error."""

    def test_fallback_on_invalid_theme(self):
        """Test fallback SVG returned when theme is None."""
        svg = SVGComposer.compose("hero-background", None)
        assert "<svg" in svg
        assert "</svg>" in svg
        assert "#F3F4F6" in svg, "Fallback should use default gray gradient"

    def test_fallback_svg_valid(self):
        """Test fallback SVG is valid (no script tags)."""
        svg = SVGComposer._fallback_svg((1920, 1080))
        assert "<svg" in svg
        assert "</svg>" in svg
        assert "<script" not in svg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
