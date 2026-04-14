"""Unit tests for SVG primitives (rect, circle, path, gradient, wave, grid)."""

import pytest

from aio.visuals.svg.composites import SVGComposer, VisualStyleConfig


class TestSVGPrimitives:
    """Test SVG primitive rendering."""

    def test_compose_hero_background(self):
        """Test hero-background composition."""
        theme = {
            "id": "test",
            "palette": {"primary": "#0EA5E9", "secondary": "#06B6D4"},
            "visual_config": VisualStyleConfig.defaults(),
        }
        svg = SVGComposer.compose("hero-background", theme)
        assert "<svg" in svg
        assert "</svg>" in svg
        assert "<script" not in svg

    def test_compose_section_divider(self):
        """Test section-divider composition."""
        theme = {
            "id": "test",
            "palette": {"primary": "#0EA5E9"},
            "visual_config": VisualStyleConfig.defaults(),
        }
        svg = SVGComposer.compose("section-divider", theme)
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_invalid_type(self):
        """Test invalid composition type raises ValueError."""
        theme = {"id": "test", "palette": {}}
        with pytest.raises(ValueError, match="Unsupported type"):
            SVGComposer.compose("invalid-type", theme)

    def test_deterministic_seed(self):
        """Test same seed produces same SVG."""
        theme = {"id": "test", "palette": {"primary": "#0EA5E9"}}
        svg1 = SVGComposer.compose("hero-background", theme, seed=12345)
        svg2 = SVGComposer.compose("hero-background", theme, seed=12345)
        assert svg1 == svg2

    def test_visual_config_defaults(self):
        """Test default visual config is applied."""
        config = VisualStyleConfig.defaults()
        assert config.visual_style_preference == "tech"
        assert config.pattern == "grid"
        assert config.curvature == "sharp"
        assert config.animation_preference == "static"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
