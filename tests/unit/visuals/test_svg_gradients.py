"""Unit tests for gradient and pattern generation."""

import pytest
from aio.visuals.svg.composites import SVGComposer, VisualStyleConfig


class TestGradientsAndPatterns:
    """Test gradient and pattern rendering."""

    def test_gradient_in_output(self):
        """Test gradient is included in SVG output."""
        theme = {
            "id": "test",
            "palette": {"primary": "#0EA5E9", "secondary": "#06B6D4"},
        }
        svg = SVGComposer.compose("hero-background", theme)
        assert "linearGradient" in svg
        assert "stop offset" in svg

    def test_color_extraction(self):
        """Test color extraction from palette."""
        palette = {"primary": "#0EA5E9", "secondary": "#06B6D4", "accent": "#14B8A6"}
        colors = SVGComposer._extract_colors(palette)
        assert len(colors) == 3
        assert colors[0] == "#0EA5E9"

    def test_fallback_colors(self):
        """Test default colors when palette is empty."""
        colors = SVGComposer._extract_colors({})
        assert len(colors) == 3
        assert colors[0] == "#0EA5E9"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
