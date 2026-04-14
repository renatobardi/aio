"""SVG Composites Engine — deterministic SVG composition from theme palettes."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

# ============================================================================
# Data Models
# ============================================================================


@dataclass
class VisualStyleConfig:
    """Visual style preferences extracted from DESIGN.md section 10."""

    visual_style_preference: Literal["geometric", "organic", "tech", "minimal"] = "tech"
    pattern: Literal["grid", "dots", "lines", "mesh", "noise", "flowing"] = "geometric"
    curvature: Literal["sharp", "soft", "mixed"] = "sharp"
    animation_preference: Literal["static", "subtle", "dynamic"] = "static"

    @classmethod
    def defaults(cls) -> VisualStyleConfig:
        """Return default visual config (tech/geometric/sharp/static) for legacy themes."""
        return cls(
            visual_style_preference="tech", pattern="geometric", curvature="sharp", animation_preference="static"
        )


@dataclass
class SVGComposite:
    """Represents a rendered SVG composition for a slide."""

    type: Literal[
        "hero-background",
        "feature-illustration",
        "stat-decoration",
        "section-divider",
        "abstract-art",
        "process-steps",
        "comparison-split",
        "grid-showcase",
    ]
    theme_id: str
    style_config: VisualStyleConfig
    dimensions: tuple[int, int] = (1920, 1080)
    svg_content: str = ""
    seed: int | None = None

    def is_valid(self) -> bool:
        """Check if SVG content is valid W3C SVG."""
        if not self.svg_content:
            return False
        return "<svg" in self.svg_content and "</svg>" in self.svg_content and "<script" not in self.svg_content


# ============================================================================
# SVGComposer Interface
# ============================================================================


class SVGComposer:
    """Main composer for generating deterministic SVG compositions."""

    SUPPORTED_TYPES = {
        "hero-background",
        "feature-illustration",
        "stat-decoration",
        "section-divider",
        "abstract-art",
        "process-steps",
        "comparison-split",
        "grid-showcase",
    }

    @staticmethod
    def compose(
        composite_type: str,
        theme: dict,  # ThemeRecord with palette and visual_config
        dimensions: tuple[int, int] = (1920, 1080),
        seed: int | None = None,
    ) -> str:
        """Generate deterministic SVG composition."""
        if composite_type not in SVGComposer.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported type: {composite_type}")

        try:
            # Extract configuration
            visual_config = theme.get("visual_config") or VisualStyleConfig.defaults()
            palette = theme.get("palette", {})
            colors = SVGComposer._extract_colors(palette)

            # Derive seed if not provided
            if seed is None:
                theme_id = theme.get("id", "unknown")
                seed_str = f"{theme_id}:{composite_type}"
                seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % (2**31)

            # Generate SVG based on type
            svg = SVGComposer._generate_svg(composite_type, colors, visual_config, dimensions, seed)
            return svg

        except Exception:
            # Return fallback SVG on error
            return SVGComposer._fallback_svg(dimensions)

    @staticmethod
    def _extract_colors(palette: dict) -> list[str]:
        """Extract primary colors from theme palette."""
        colors = []
        if "primary" in palette:
            colors.append(palette["primary"])
        if "secondary" in palette:
            colors.append(palette["secondary"])
        if "accent" in palette:
            colors.append(palette["accent"])
        if not colors:
            colors = ["#0EA5E9", "#06B6D4", "#14B8A6"]
        return colors[:3]

    @staticmethod
    def _generate_svg(
        composite_type: str,
        colors: list[str],
        visual_config: VisualStyleConfig | dict,
        dimensions: tuple[int, int],
        seed: int,
    ) -> str:
        """
        Generate SVG content based on type and visual configuration.

        visual_config heuristics:
        - tech → grids, straight lines, sharp angles
        - organic → curves, waves, soft edges
        - minimal → sparse, high contrast
        - geometric → structured, symmetrical
        """
        width, height = dimensions
        gradient_id = f"grad_{seed % 1000}"

        # Normalize visual_config to dict if it's a dataclass
        if not isinstance(visual_config, dict):
            visual_config = {
                "visual_style_preference": getattr(visual_config, "visual_style_preference", "tech"),
                "pattern": getattr(visual_config, "pattern", "geometric"),
                "curvature": getattr(visual_config, "curvature", "sharp"),
                "animation_preference": getattr(visual_config, "animation_preference", "static"),
            }

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
            "<defs>",
            SVGComposer._create_gradient(gradient_id, colors),
            "</defs>",
            f'<rect width="{width}" height="{height}" fill="url(#{gradient_id})" opacity="0.95"/>',
        ]

        # Apply visual config heuristics based on style preference
        style_pref = visual_config.get("visual_style_preference", "tech")

        if composite_type == "hero-background":
            svg_parts.append(SVGComposer._hero_background(colors, width, height, visual_config))
        elif style_pref == "tech":
            svg_parts.append(SVGComposer._grid_pattern(colors, width, height, seed))
        elif style_pref == "organic":
            svg_parts.append(SVGComposer._wave_pattern(colors, width, height, seed))
        elif style_pref == "minimal":
            svg_parts.append(SVGComposer._sparse_pattern(colors, width, height))
        else:  # geometric
            svg_parts.append(SVGComposer._geometric_pattern(colors, width, height, seed))

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)

    @staticmethod
    def _create_gradient(gradient_id: str, colors: list[str]) -> str:
        """Create linear gradient definition."""
        c1, c2 = colors[0], colors[1] if len(colors) > 1 else colors[0]
        return (
            f'<linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="100%">'
            f'<stop offset="0%" style="stop-color:{c1};stop-opacity:1" />'
            f'<stop offset="100%" style="stop-color:{c2};stop-opacity:0.7" />'
            "</linearGradient>"
        )

    @staticmethod
    def _hero_background(colors: list[str], width: int, height: int, visual_config: dict | None = None) -> str:
        """Generate hero-background composition, varying by visual preference."""
        c1 = colors[0]
        style = (visual_config or {}).get("visual_style_preference", "tech") if visual_config else "tech"

        if style == "organic":
            # Soft, flowing organic shape
            return (
                f'<ellipse cx="{width // 2}" cy="{height // 2}" rx="{width // 3}" '
                f'ry="{height // 3}" fill="{c1}" opacity="0.15"/>'
            )
        else:
            # Tech/geometric: sharp circle
            return (
                f'<circle cx="{width // 2}" cy="{height // 2}" r="{min(width, height) // 3}" '
                f'fill="{c1}" opacity="0.2"/>'
            )

    @staticmethod
    def _grid_pattern(colors: list[str], width: int, height: int, seed: int) -> str:
        """Generate tech-style grid pattern (straight lines, sharp angles)."""
        c1 = colors[0]
        lines = []
        spacing = 100
        # Vertical lines
        for x in range(0, width + spacing, spacing):
            line = f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="{c1}" stroke-width="1" opacity="0.1"/>'
            lines.append(line)
        # Horizontal lines
        for y in range(0, height + spacing, spacing):
            line = f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="{c1}" stroke-width="1" opacity="0.1"/>'
            lines.append(line)
        return "\n".join(lines[:30])

    @staticmethod
    def _wave_pattern(colors: list[str], width: int, height: int, seed: int) -> str:
        """Generate organic-style wave pattern with curves."""
        c1 = colors[0]
        # Simple wave using quadratic curves
        points = []
        for x in range(0, width + 100, 100):
            hash_val = hashlib.sha256(f"{seed}{x}".encode()).hexdigest()[:4]
            y = height // 2 + int(50 * int(hash_val, 16)) % 100 - 50
            points.append(f"{x},{y}")
        path = " ".join(points)
        return (
            f'<polyline points="{path}" fill="none" stroke="{c1}" '
            f'stroke-width="3" opacity="0.3" stroke-linecap="round"/>'
        )

    @staticmethod
    def _sparse_pattern(colors: list[str], width: int, height: int) -> str:
        """Generate minimal-style sparse pattern (few elements, high contrast)."""
        c1 = colors[0]
        elements = []
        # Just 4 strategic circles
        positions = [
            (width // 4, height // 4),
            (3 * width // 4, height // 4),
            (width // 4, 3 * height // 4),
            (3 * width // 4, 3 * height // 4),
        ]
        for x, y in positions:
            elements.append(f'<circle cx="{x}" cy="{y}" r="30" fill="{c1}" opacity="0.25"/>')
        return "\n".join(elements)

    @staticmethod
    def _geometric_pattern(colors: list[str], width: int, height: int, seed: int) -> str:
        """Generate geometric-style structured pattern (shapes, symmetry)."""
        c1 = colors[0]
        elements = []
        # Regular grid of rectangles
        size = 60
        for y in range(0, height, size):
            for x in range(0, width, size):
                if (x // size + y // size) % 2 == 0:
                    rect = f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="{c1}" opacity="0.08"/>'
                    elements.append(rect)
        return "\n".join(elements[:40])

    @staticmethod
    def _generic_pattern(colors: list[str], width: int, height: int) -> str:
        """Generate generic pattern (fallback)."""
        c1 = colors[0]
        dots = []
        for y in range(25, height, 50):
            for x in range(25, width, 50):
                dots.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{c1}" opacity="0.15"/>')
        return "\n".join(dots[:20])

    @staticmethod
    def _fallback_svg(dimensions: tuple[int, int]) -> str:
        """Return minimum valid SVG fallback."""
        width, height = dimensions
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
            '<defs><linearGradient id="fallback" x1="0%" y1="0%" x2="100%" y2="100%">'
            '<stop offset="0%" style="stop-color:#F3F4F6;stop-opacity:1" />'
            '<stop offset="100%" style="stop-color:#E5E7EB;stop-opacity:1" />'
            "</linearGradient></defs>"
            f'<rect width="{width}" height="{height}" fill="url(#fallback)"/>'
            "</svg>"
        )
