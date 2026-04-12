"""Unit tests for dataviz SVG chart generation (TDD — 30+ cases)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from aio.visuals.dataviz.charts import (
    BarChart,
    HeatmapChart,
    LineChart,
    PieChart,
    ScatterChart,
    render_chart,
)
from aio.visuals.dataviz.data_parser import ChartData, Series

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bar(labels: list[str] | None = None, series: list[Series] | None = None) -> ChartData:
    return ChartData(
        chart_type="bar",
        series=series or [Series(name="A", values=[10.0, 20.0, 30.0])],
        labels=labels or ["Q1", "Q2", "Q3"],
    )


def _line(labels: list[str] | None = None) -> ChartData:
    return ChartData(
        chart_type="line",
        series=[Series(name="A", values=[1.0, 4.0, 9.0])],
        labels=labels or ["Jan", "Feb", "Mar"],
    )


def _pie() -> ChartData:
    return ChartData(
        chart_type="pie",
        series=[Series(name="Breakdown", values=[30.0, 50.0, 20.0])],
        labels=["A", "B", "C"],
    )


def _scatter() -> ChartData:
    return ChartData(
        chart_type="scatter",
        series=[Series(name="Points", values=[1.0, 2.0, 3.0, 4.0])],
        labels=["1.0", "1.5", "2.0", "2.5"],
    )


def _heatmap() -> ChartData:
    return ChartData(
        chart_type="heatmap",
        series=[
            Series(name="Row0", values=[0.1, 0.5, 0.9]),
            Series(name="Row1", values=[0.3, 0.7, 0.2]),
        ],
        labels=["C1", "C2", "C3"],
    )


def _assert_valid_svg(svg: str) -> ET.Element:
    """Assert SVG is well-formed XML and return root element."""
    assert svg.startswith("<svg"), f"Expected SVG to start with '<svg', got: {svg[:50]}"
    root = ET.fromstring(svg)
    return root


# ---------------------------------------------------------------------------
# SVG contract — applies to ALL chart types
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "data",
    [_bar(), _line(), _pie(), _scatter(), _heatmap()],
    ids=["bar", "line", "pie", "scatter", "heatmap"],
)
def test_svg_contract_starts_with_svg_tag(data: ChartData) -> None:
    svg = render_chart(data)
    assert svg.strip().startswith("<svg")


@pytest.mark.parametrize(
    "data",
    [_bar(), _line(), _pie(), _scatter(), _heatmap()],
    ids=["bar", "line", "pie", "scatter", "heatmap"],
)
def test_svg_contract_has_xmlns(data: ChartData) -> None:
    svg = render_chart(data)
    assert "xmlns" in svg


@pytest.mark.parametrize(
    "data",
    [_bar(), _line(), _pie(), _scatter(), _heatmap()],
    ids=["bar", "line", "pie", "scatter", "heatmap"],
)
def test_svg_contract_has_role_img(data: ChartData) -> None:
    svg = render_chart(data)
    assert 'role="img"' in svg


@pytest.mark.parametrize(
    "data",
    [_bar(), _line(), _pie(), _scatter(), _heatmap()],
    ids=["bar", "line", "pie", "scatter", "heatmap"],
)
def test_svg_contract_has_title_element(data: ChartData) -> None:
    svg = render_chart(data)
    assert "<title>" in svg


@pytest.mark.parametrize(
    "data",
    [_bar(), _line(), _pie(), _scatter(), _heatmap()],
    ids=["bar", "line", "pie", "scatter", "heatmap"],
)
def test_svg_contract_no_script_tag(data: ChartData) -> None:
    svg = render_chart(data)
    assert "<script" not in svg.lower()


@pytest.mark.parametrize(
    "data",
    [_bar(), _line(), _pie(), _scatter(), _heatmap()],
    ids=["bar", "line", "pie", "scatter", "heatmap"],
)
def test_svg_contract_parseable_xml(data: ChartData) -> None:
    svg = render_chart(data)
    root = _assert_valid_svg(svg)
    assert root.tag.endswith("svg")


# ---------------------------------------------------------------------------
# BarChart
# ---------------------------------------------------------------------------


def test_bar_chart_renders_rects() -> None:
    svg = BarChart(_bar()).render()
    assert "<rect" in svg


def test_bar_chart_title_in_svg() -> None:
    data = _bar()
    data.title = "Revenue"
    svg = BarChart(data).render()
    assert "Revenue" in svg


def test_bar_chart_multiple_series() -> None:
    data = ChartData(
        chart_type="bar",
        series=[
            Series(name="A", values=[1.0, 2.0]),
            Series(name="B", values=[3.0, 4.0]),
        ],
        labels=["X", "Y"],
    )
    svg = BarChart(data).render()
    _assert_valid_svg(svg)
    assert "<rect" in svg


def test_bar_chart_custom_size() -> None:
    data = ChartData(
        chart_type="bar",
        series=[Series(name="A", values=[1.0])],
        width=640,
        height=360,
    )
    svg = BarChart(data).render()
    assert "640" in svg and "360" in svg


# ---------------------------------------------------------------------------
# LineChart
# ---------------------------------------------------------------------------


def test_line_chart_renders_polyline_or_path() -> None:
    svg = LineChart(_line()).render()
    assert "<polyline" in svg or "<path" in svg


def test_line_chart_title_in_svg() -> None:
    data = _line()
    data.title = "Trend"
    svg = LineChart(data).render()
    assert "Trend" in svg


def test_line_chart_xml_valid() -> None:
    svg = LineChart(_line()).render()
    _assert_valid_svg(svg)


# ---------------------------------------------------------------------------
# PieChart
# ---------------------------------------------------------------------------


def test_pie_chart_renders_path_or_circle() -> None:
    svg = PieChart(_pie()).render()
    assert "<path" in svg or "<circle" in svg


def test_pie_chart_xml_valid() -> None:
    svg = PieChart(_pie()).render()
    _assert_valid_svg(svg)


def test_pie_chart_single_value_full_circle() -> None:
    data = ChartData(
        chart_type="pie",
        series=[Series(name="All", values=[100.0])],
    )
    svg = PieChart(data).render()
    _assert_valid_svg(svg)


# ---------------------------------------------------------------------------
# ScatterChart
# ---------------------------------------------------------------------------


def test_scatter_chart_renders_circles() -> None:
    svg = ScatterChart(_scatter()).render()
    assert "<circle" in svg


def test_scatter_chart_xml_valid() -> None:
    svg = ScatterChart(_scatter()).render()
    _assert_valid_svg(svg)


# ---------------------------------------------------------------------------
# HeatmapChart
# ---------------------------------------------------------------------------


def test_heatmap_chart_renders_rects() -> None:
    svg = HeatmapChart(_heatmap()).render()
    assert "<rect" in svg


def test_heatmap_chart_xml_valid() -> None:
    svg = HeatmapChart(_heatmap()).render()
    _assert_valid_svg(svg)


# ---------------------------------------------------------------------------
# render_chart factory
# ---------------------------------------------------------------------------


def test_render_chart_bar() -> None:
    svg = render_chart(_bar())
    assert "<rect" in svg


def test_render_chart_line() -> None:
    svg = render_chart(_line())
    assert "<polyline" in svg or "<path" in svg


def test_render_chart_pie() -> None:
    svg = render_chart(_pie())
    _assert_valid_svg(svg)


def test_render_chart_scatter() -> None:
    svg = render_chart(_scatter())
    assert "<circle" in svg


def test_render_chart_heatmap() -> None:
    svg = render_chart(_heatmap())
    assert "<rect" in svg


def test_render_chart_output_is_sanitized_no_script() -> None:
    data = _bar()
    svg = render_chart(data)
    assert "<script" not in svg.lower()
