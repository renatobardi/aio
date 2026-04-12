"""Pure-Python SVG chart generation — no external charting deps.

Exports:
    BaseChart, BarChart, LineChart, PieChart, ScatterChart, HeatmapChart
    render_chart()  — factory that dispatches to the right class
"""

from __future__ import annotations

import abc
import math
import xml.etree.ElementTree as ET
from typing import Any

from aio.visuals.dataviz.data_parser import ChartData, Series

# Default palette used when a Series has no color set
_PALETTE = [
    "#4C72B0",
    "#DD8452",
    "#55A868",
    "#C44E52",
    "#8172B3",
    "#937860",
    "#DA8BC3",
    "#8C8C8C",
    "#CCB974",
    "#64B5CD",
]

_SVG_NS = "http://www.w3.org/2000/svg"  # NOSONAR — W3C namespace URI, not a fetchable URL


# ---------------------------------------------------------------------------
# Internal SVG builder helper
# ---------------------------------------------------------------------------


class _SVGBuilder:
    """Minimal helper that builds an SVG string via ElementTree."""

    def __init__(self, width: int, height: int, title: str | None = None) -> None:
        ET.register_namespace("", _SVG_NS)
        self._root = ET.Element(
            f"{{{_SVG_NS}}}svg",
            {
                "width": str(width),
                "height": str(height),
                "viewBox": f"0 0 {width} {height}",
                "role": "img",
            },
        )
        t = ET.SubElement(self._root, f"{{{_SVG_NS}}}title")
        t.text = title or "Chart"

    def add(self, tag: str, attribs: dict[str, str], text: str | None = None) -> ET.Element:
        el = ET.SubElement(self._root, f"{{{_SVG_NS}}}{tag}", attribs)
        if text is not None:
            el.text = text
        return el

    def add_to(
        self,
        parent: ET.Element,
        tag: str,
        attribs: dict[str, str],
        text: str | None = None,
    ) -> ET.Element:
        el = ET.SubElement(parent, f"{{{_SVG_NS}}}{tag}", attribs)
        if text is not None:
            el.text = text
        return el

    def build(self) -> str:
        return ET.tostring(self._root, encoding="unicode", xml_declaration=False)


def _color(series: Series, idx: int) -> str:
    return series.color or _PALETTE[idx % len(_PALETTE)]


def _sanitize(svg: str) -> str:
    """Reuse CompositionEngine.sanitize_svg to strip <script> and event attrs."""
    from aio.composition.engine import CompositionEngine

    return CompositionEngine.sanitize_svg(svg)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class BaseChart(abc.ABC):
    """Abstract base for all chart types."""

    def __init__(self, data: ChartData) -> None:
        self._data = data

    @abc.abstractmethod
    def _draw(self, b: _SVGBuilder) -> None:
        """Populate the SVG builder with chart-specific elements."""

    def render(self) -> str:
        """Return sanitized SVG string."""
        b = _SVGBuilder(self._data.width, self._data.height, self._data.title)
        self._draw(b)
        return _sanitize(b.build())


# ---------------------------------------------------------------------------
# BarChart
# ---------------------------------------------------------------------------


class BarChart(BaseChart):
    """Grouped vertical bar chart."""

    _MARGIN = {"top": 40, "right": 20, "bottom": 50, "left": 50}

    def _draw(self, b: _SVGBuilder) -> None:  # noqa: PLR0912
        data = self._data
        m = self._MARGIN
        chart_w = data.width - m["left"] - m["right"]
        chart_h = data.height - m["top"] - m["bottom"]

        n_groups = max(len(s.values) for s in data.series)
        n_series = len(data.series)
        group_w = chart_w / max(n_groups, 1)
        bar_w = group_w / max(n_series + 1, 2)

        all_values = [v for s in data.series for v in s.values]
        max_val = max(all_values) if all_values else 1.0
        if max_val == 0:
            max_val = 1.0

        g: ET.Element = b.add("g", {"transform": f"translate({m['left']},{m['top']})"})

        # Axes
        b.add_to(
            g,
            "line",
            {
                "x1": "0",
                "y1": str(chart_h),
                "x2": str(chart_w),
                "y2": str(chart_h),
                "stroke": "#999",
                "stroke-width": "1",
            },
        )
        b.add_to(
            g,
            "line",
            {
                "x1": "0",
                "y1": "0",
                "x2": "0",
                "y2": str(chart_h),
                "stroke": "#999",
                "stroke-width": "1",
            },
        )

        for si, series in enumerate(data.series):
            color = _color(series, si)
            for gi, val in enumerate(series.values):
                bar_h = (val / max_val) * chart_h
                x = gi * group_w + si * bar_w + bar_w * 0.5
                y = chart_h - bar_h
                b.add_to(
                    g,
                    "rect",
                    {
                        "x": f"{x:.1f}",
                        "y": f"{y:.1f}",
                        "width": f"{bar_w:.1f}",
                        "height": f"{bar_h:.1f}",
                        "fill": color,
                        "opacity": "0.85",
                    },
                )

        # X-axis labels
        for gi, label in enumerate(data.labels[:n_groups]):
            x = gi * group_w + group_w * 0.5
            b.add_to(
                g,
                "text",
                {
                    "x": f"{x:.1f}",
                    "y": str(chart_h + 20),
                    "text-anchor": "middle",
                    "font-size": "12",
                    "fill": "#555",
                },
                label,
            )


# ---------------------------------------------------------------------------
# LineChart
# ---------------------------------------------------------------------------


class LineChart(BaseChart):
    """Multi-series line chart using polyline elements."""

    _MARGIN = {"top": 40, "right": 20, "bottom": 50, "left": 50}

    def _draw(self, b: _SVGBuilder) -> None:
        data = self._data
        m = self._MARGIN
        chart_w = data.width - m["left"] - m["right"]
        chart_h = data.height - m["top"] - m["bottom"]

        n_points = max(len(s.values) for s in data.series)
        all_values = [v for s in data.series for v in s.values]
        max_val = max(all_values) if all_values else 1.0
        min_val = min(all_values) if all_values else 0.0
        val_range = max_val - min_val or 1.0

        g: ET.Element = b.add("g", {"transform": f"translate({m['left']},{m['top']})"})

        # Axes
        b.add_to(
            g,
            "line",
            {"x1": "0", "y1": str(chart_h), "x2": str(chart_w), "y2": str(chart_h), "stroke": "#999"},
        )
        b.add_to(
            g,
            "line",
            {"x1": "0", "y1": "0", "x2": "0", "y2": str(chart_h), "stroke": "#999"},
        )

        step = chart_w / max(n_points - 1, 1)

        for si, series in enumerate(data.series):
            color = _color(series, si)
            if len(series.values) < 2:
                continue
            pts = " ".join(
                f"{i * step:.1f},{chart_h - ((v - min_val) / val_range) * chart_h:.1f}"
                for i, v in enumerate(series.values)
            )
            b.add_to(
                g,
                "polyline",
                {
                    "points": pts,
                    "fill": "none",
                    "stroke": color,
                    "stroke-width": "2",
                    "stroke-linejoin": "round",
                },
            )

        # X-axis labels
        for gi, label in enumerate(data.labels[:n_points]):
            x = gi * step
            b.add_to(
                g,
                "text",
                {
                    "x": f"{x:.1f}",
                    "y": str(chart_h + 18),
                    "text-anchor": "middle",
                    "font-size": "11",
                    "fill": "#555",
                },
                label,
            )


# ---------------------------------------------------------------------------
# PieChart
# ---------------------------------------------------------------------------


class PieChart(BaseChart):
    """Pie / donut chart using SVG path arc commands."""

    def _draw(self, b: _SVGBuilder) -> None:
        data = self._data
        cx = data.width / 2
        cy = data.height / 2
        r = min(cx, cy) * 0.75

        values = data.series[0].values if data.series else []
        total = sum(values) or 1.0

        if len(values) == 1:
            # Full circle
            color = _color(data.series[0], 0) if data.series else _PALETTE[0]
            b.add(
                "circle",
                {
                    "cx": f"{cx:.1f}",
                    "cy": f"{cy:.1f}",
                    "r": f"{r:.1f}",
                    "fill": color,
                },
            )
            return

        start_angle = -math.pi / 2
        for idx, val in enumerate(values):
            sweep = (val / total) * 2 * math.pi
            end_angle = start_angle + sweep

            x1 = cx + r * math.cos(start_angle)
            y1 = cy + r * math.sin(start_angle)
            x2 = cx + r * math.cos(end_angle)
            y2 = cy + r * math.sin(end_angle)

            large_arc = "1" if sweep > math.pi else "0"
            color = _color(data.series[0] if data.series else Series("", []), idx)

            path_d = f"M {cx:.1f} {cy:.1f} L {x1:.1f} {y1:.1f} A {r:.1f} {r:.1f} 0 {large_arc} 1 {x2:.1f} {y2:.1f} Z"
            b.add("path", {"d": path_d, "fill": color, "stroke": "#fff", "stroke-width": "1"})
            start_angle = end_angle


# ---------------------------------------------------------------------------
# ScatterChart
# ---------------------------------------------------------------------------


class ScatterChart(BaseChart):
    """Scatter plot — treats Series.values as y-coordinates; labels as x-values."""

    _MARGIN = {"top": 40, "right": 20, "bottom": 50, "left": 50}

    def _draw(self, b: _SVGBuilder) -> None:
        data = self._data
        m = self._MARGIN
        chart_w = data.width - m["left"] - m["right"]
        chart_h = data.height - m["top"] - m["bottom"]

        all_y = [v for s in data.series for v in s.values]
        max_y = max(all_y) if all_y else 1.0
        min_y = min(all_y) if all_y else 0.0
        y_range = max_y - min_y or 1.0

        # Parse x from labels; fall back to index
        def _x_vals(n: int) -> list[float]:
            xs: list[float] = []
            for i in range(n):
                try:
                    xs.append(float(data.labels[i]))
                except (IndexError, ValueError):
                    xs.append(float(i))
            return xs

        x_vals_raw: list[float] = []
        for s in data.series:
            x_vals_raw.extend(_x_vals(len(s.values)))

        max_x = max(x_vals_raw) if x_vals_raw else 1.0
        min_x = min(x_vals_raw) if x_vals_raw else 0.0
        x_range = max_x - min_x or 1.0

        g: ET.Element = b.add("g", {"transform": f"translate({m['left']},{m['top']})"})
        b.add_to(g, "line", {"x1": "0", "y1": str(chart_h), "x2": str(chart_w), "y2": str(chart_h), "stroke": "#999"})
        b.add_to(g, "line", {"x1": "0", "y1": "0", "x2": "0", "y2": str(chart_h), "stroke": "#999"})

        for si, series in enumerate(data.series):
            color = _color(series, si)
            xs = _x_vals(len(series.values))
            for xi, yi in zip(xs, series.values):
                px = ((xi - min_x) / x_range) * chart_w
                py = chart_h - ((yi - min_y) / y_range) * chart_h
                b.add_to(
                    g,
                    "circle",
                    {"cx": f"{px:.1f}", "cy": f"{py:.1f}", "r": "4", "fill": color, "opacity": "0.75"},
                )


# ---------------------------------------------------------------------------
# HeatmapChart
# ---------------------------------------------------------------------------


class HeatmapChart(BaseChart):
    """Heatmap — series.values are row cell values (0.0–1.0 normalized or raw)."""

    _MARGIN = {"top": 40, "right": 20, "bottom": 50, "left": 60}

    def _draw(self, b: _SVGBuilder) -> None:
        data = self._data
        m = self._MARGIN
        chart_w = data.width - m["left"] - m["right"]
        chart_h = data.height - m["top"] - m["bottom"]

        n_rows = len(data.series)
        n_cols = max((len(s.values) for s in data.series), default=1)

        all_vals = [v for s in data.series for v in s.values]
        max_v = max(all_vals) if all_vals else 1.0
        min_v = min(all_vals) if all_vals else 0.0
        v_range = max_v - min_v or 1.0

        cell_w = chart_w / max(n_cols, 1)
        cell_h = chart_h / max(n_rows, 1)

        g: ET.Element = b.add("g", {"transform": f"translate({m['left']},{m['top']})"})

        for ri, series in enumerate(data.series):
            for ci, val in enumerate(series.values):
                norm = (val - min_v) / v_range
                # Map 0→light blue, 1→dark blue
                intensity = int(norm * 200)
                fill = f"rgb({50},{100 + intensity // 2},{155 + intensity // 2})"
                b.add_to(
                    g,
                    "rect",
                    {
                        "x": f"{ci * cell_w:.1f}",
                        "y": f"{ri * cell_h:.1f}",
                        "width": f"{cell_w - 1:.1f}",
                        "height": f"{cell_h - 1:.1f}",
                        "fill": fill,
                    },
                )

        # Column labels
        for ci, label in enumerate(data.labels[:n_cols]):
            b.add_to(
                g,
                "text",
                {
                    "x": f"{ci * cell_w + cell_w / 2:.1f}",
                    "y": str(chart_h + 18),
                    "text-anchor": "middle",
                    "font-size": "11",
                    "fill": "#555",
                },
                label,
            )

        # Row labels
        for ri, series in enumerate(data.series):
            b.add_to(
                g,
                "text",
                {
                    "x": "-5",
                    "y": f"{ri * cell_h + cell_h / 2:.1f}",
                    "text-anchor": "end",
                    "dominant-baseline": "middle",
                    "font-size": "11",
                    "fill": "#555",
                },
                series.name,
            )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_CHART_CLASSES: dict[str, type[BaseChart]] = {
    "bar": BarChart,
    "line": LineChart,
    "pie": PieChart,
    "scatter": ScatterChart,
    "heatmap": HeatmapChart,
}


def render_chart(data: ChartData) -> str:
    """Factory: dispatch to the correct chart class and return sanitized SVG."""
    cls = _CHART_CLASSES.get(data.chart_type)
    if cls is None:
        from aio.exceptions import ChartDataError

        raise ChartDataError(f"Unknown chart type: {data.chart_type}", chart_type=data.chart_type)
    return cls(data).render()


# Expose Any to satisfy mypy for _SVGBuilder._add_to return type hints
__all__ = [
    "BaseChart",
    "BarChart",
    "LineChart",
    "PieChart",
    "ScatterChart",
    "HeatmapChart",
    "render_chart",
]
_: Any  # suppress unused import warning for typing
