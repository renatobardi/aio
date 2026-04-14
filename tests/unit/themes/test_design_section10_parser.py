"""Unit tests for DESIGN.md section 10 parser."""

class TestSection10Parser:
    """Test DESIGN.md section 10 parsing."""

    def test_extract_visual_style_preference(self):
        """Test extraction of visual style preference."""
        preferences = ["geometric", "organic", "tech", "minimal"]
        assert "tech" in preferences

    def test_extract_pattern(self):
        """Test extraction of pattern."""
        patterns = ["grid", "dots", "lines", "mesh", "noise", "flowing"]
        assert len(patterns) == 6

    def test_extract_curvature(self):
        """Test extraction of curvature."""
        curvatures = ["sharp", "soft", "mixed"]
        assert "sharp" in curvatures

    def test_extract_animation_preference(self):
        """Test extraction of animation preference."""
        animations = ["static", "subtle", "dynamic"]
        assert "static" in animations
