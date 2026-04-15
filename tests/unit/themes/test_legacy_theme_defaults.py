"""Unit tests for legacy theme default generation."""

from aio.visuals.svg.composites import VisualStyleConfig


class TestLegacyThemeDefaults:
    """Test auto-generation of defaults for legacy themes."""

    def test_default_config_tech_geometric_sharp(self):
        """Test defaults are tech/grid/sharp/static."""
        config = VisualStyleConfig.defaults()
        assert config.visual_style_preference == "tech"
        assert config.pattern == "grid"
        assert config.curvature == "sharp"
        assert config.animation_preference == "static"

    def test_all_fields_present(self):
        """Test all required fields are present."""
        config = VisualStyleConfig.defaults()
        assert hasattr(config, "visual_style_preference")
        assert hasattr(config, "pattern")
        assert hasattr(config, "curvature")
        assert hasattr(config, "animation_preference")
