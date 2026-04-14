"""Integration tests for all 8 SVG composite types."""

import pytest

from aio.visuals.svg.composites import SVGComposer


class TestSVGCompositeTypes:
    """Test all 8 SVG composite types render successfully."""

    COMPOSITE_TYPES = [
        "hero-background",
        "feature-illustration",
        "stat-decoration",
        "section-divider",
        "abstract-art",
        "process-steps",
        "comparison-split",
        "grid-showcase",
    ]

    @pytest.mark.parametrize("comp_type", COMPOSITE_TYPES)
    def test_all_types_render(self, comp_type):
        """Test all 8 types render without error."""
        theme = {
            "id": "test-theme",
            "palette": {"primary": "#0EA5E9", "secondary": "#06B6D4"},
        }
        svg = SVGComposer.compose(comp_type, theme)
        assert "<svg" in svg
        assert "</svg>" in svg
        assert "<script" not in svg, f"SVG should not contain script tags for {comp_type}"

    def test_svg_size_constraint(self):
        """Test SVG output is ≤20 KB."""
        theme = {"id": "test", "palette": {"primary": "#0EA5E9"}}
        import gzip
        svg = SVGComposer.compose("hero-background", theme)
        gzipped = gzip.compress(svg.encode())
        assert len(gzipped) <= 20000, f"SVG size {len(gzipped)} bytes exceeds 20 KB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
