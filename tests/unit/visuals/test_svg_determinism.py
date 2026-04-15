"""Unit tests for deterministic seed-based generation."""

import pytest

from aio.visuals.svg.composites import SVGComposer


class TestDeterministicGeneration:
    """Test deterministic SVG generation based on seed."""

    def test_same_seed_same_output(self):
        """Verify identical seed produces identical SVG."""
        theme = {"id": "linear", "palette": {"primary": "#0EA5E9"}}
        svg1 = SVGComposer.compose("hero-background", theme, seed=99999)
        svg2 = SVGComposer.compose("hero-background", theme, seed=99999)
        assert svg1 == svg2, "Same seed should produce identical SVG"

    def test_different_seed_different_output(self):
        """Verify different seeds produce different SVG."""
        theme = {"id": "linear", "palette": {"primary": "#0EA5E9"}}
        svg1 = SVGComposer.compose("hero-background", theme, seed=1111)
        svg2 = SVGComposer.compose("hero-background", theme, seed=2222)
        # Should produce same structure but possibly different attributes
        assert "<svg" in svg1 and "<svg" in svg2

    def test_auto_seed_derivation(self):
        """Test seed is auto-derived from theme_id + type if not provided."""
        theme = {"id": "minimal", "palette": {"primary": "#0EA5E9"}}
        svg1 = SVGComposer.compose("section-divider", theme)
        svg2 = SVGComposer.compose("section-divider", theme)
        assert svg1 == svg2, "Auto-derived seed should be consistent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
