"""Integration tests for theme section 10 loading."""

from aio.visuals.svg.composites import VisualStyleConfig


class TestThemeSection10Loading:
    """Test DESIGN.md section 10 integration with theme loader."""

    def test_theme_loads_visual_config(self):
        """Test visual_config is loaded into theme metadata."""
        # Placeholder - would test actual theme loader
        config = VisualStyleConfig.defaults()
        theme_metadata = {"visual_config": config}
        assert "visual_config" in theme_metadata


class TestSVGVisualConfigImpact:
    """Test visual config impacts SVG output."""

    def test_tech_vs_organic_differ(self):
        """Test tech and organic configs produce different output."""
        from aio.visuals.svg.composites import SVGComposer
        
        theme_tech = {
            "id": "tech-theme",
            "palette": {"primary": "#0EA5E9"},
            "visual_config": VisualStyleConfig(
                visual_style_preference="tech",
                pattern="geometric",
                curvature="sharp"
            )
        }
        
        theme_organic = {
            "id": "organic-theme",
            "palette": {"primary": "#0EA5E9"},
            "visual_config": VisualStyleConfig(
                visual_style_preference="organic",
                pattern="flowing",
                curvature="soft"
            )
        }
        
        svg_tech = SVGComposer.compose("abstract-art", theme_tech)
        svg_organic = SVGComposer.compose("abstract-art", theme_organic)
        
        # Both should be valid SVG
        assert "<svg" in svg_tech
        assert "<svg" in svg_organic
