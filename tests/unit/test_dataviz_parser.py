"""Unit tests for dataviz data_parser — ChartData, Series, parse_chart_data() (TDD)."""

from __future__ import annotations

import json

import pytest

from aio.exceptions import ChartDataError
from aio.visuals.dataviz.data_parser import ChartData, Series, parse_chart_data

# ---------------------------------------------------------------------------
# Series
# ---------------------------------------------------------------------------


def test_series_basic() -> None:
    s = Series(name="Revenue", values=[10.0, 20.0, 30.0])
    assert s.name == "Revenue"
    assert s.values == [10.0, 20.0, 30.0]
    assert s.color is None


def test_series_with_color() -> None:
    s = Series(name="Revenue", values=[1.0], color="#ff0000")
    assert s.color == "#ff0000"


# ---------------------------------------------------------------------------
# ChartData defaults
# ---------------------------------------------------------------------------


def test_chartdata_defaults() -> None:
    cd = ChartData(
        chart_type="bar",
        series=[Series(name="A", values=[1.0, 2.0])],
    )
    assert cd.labels == []
    assert cd.title is None
    assert cd.width == 800
    assert cd.height == 450


def test_chartdata_with_labels_and_title() -> None:
    cd = ChartData(
        chart_type="line",
        series=[Series(name="A", values=[1.0])],
        labels=["Jan"],
        title="My Chart",
        width=640,
        height=360,
    )
    assert cd.labels == ["Jan"]
    assert cd.title == "My Chart"
    assert cd.width == 640
    assert cd.height == 360


# ---------------------------------------------------------------------------
# parse_chart_data — from dict
# ---------------------------------------------------------------------------


def test_parse_from_dict_minimal() -> None:
    source = {
        "series": [{"name": "A", "values": [1, 2, 3]}],
    }
    cd = parse_chart_data(source, chart_type="bar")
    assert cd.chart_type == "bar"
    assert len(cd.series) == 1
    assert cd.series[0].name == "A"
    assert cd.series[0].values == [1.0, 2.0, 3.0]


def test_parse_from_dict_with_labels() -> None:
    source = {
        "labels": ["Q1", "Q2", "Q3"],
        "series": [{"name": "Rev", "values": [10, 20, 15]}],
    }
    cd = parse_chart_data(source, chart_type="bar")
    assert cd.labels == ["Q1", "Q2", "Q3"]


def test_parse_from_dict_series_color() -> None:
    source = {
        "series": [{"name": "A", "values": [1], "color": "#abc123"}],
    }
    cd = parse_chart_data(source, chart_type="pie")
    assert cd.series[0].color == "#abc123"


def test_parse_from_dict_title_override() -> None:
    source = {"series": [{"name": "A", "values": [1]}], "title": "from dict"}
    cd = parse_chart_data(source, chart_type="bar", title="override")
    assert cd.title == "override"


def test_parse_from_dict_title_from_source() -> None:
    source = {"series": [{"name": "A", "values": [1]}], "title": "from dict"}
    cd = parse_chart_data(source, chart_type="bar")
    assert cd.title == "from dict"


def test_parse_from_dict_multiple_series() -> None:
    source = {
        "series": [
            {"name": "A", "values": [1, 2]},
            {"name": "B", "values": [3, 4]},
        ]
    }
    cd = parse_chart_data(source, chart_type="line")
    assert len(cd.series) == 2
    assert cd.series[1].name == "B"


# ---------------------------------------------------------------------------
# parse_chart_data — from JSON string
# ---------------------------------------------------------------------------


def test_parse_from_json_string() -> None:
    payload = json.dumps({"series": [{"name": "X", "values": [5, 10]}]})
    cd = parse_chart_data(payload, chart_type="bar")
    assert cd.series[0].values == [5.0, 10.0]


def test_parse_from_json_string_with_labels() -> None:
    payload = json.dumps({
        "labels": ["a", "b"],
        "series": [{"name": "S", "values": [1, 2]}],
    })
    cd = parse_chart_data(payload, chart_type="line")
    assert cd.labels == ["a", "b"]


# ---------------------------------------------------------------------------
# parse_chart_data — chart_type from source dict
# ---------------------------------------------------------------------------


def test_chart_type_from_source() -> None:
    source = {"chart_type": "pie", "series": [{"name": "A", "values": [1]}]}
    cd = parse_chart_data(source)
    assert cd.chart_type == "pie"


def test_chart_type_kwarg_overrides_source() -> None:
    source = {"chart_type": "pie", "series": [{"name": "A", "values": [1]}]}
    cd = parse_chart_data(source, chart_type="bar")
    assert cd.chart_type == "bar"


# ---------------------------------------------------------------------------
# parse_chart_data — error paths
# ---------------------------------------------------------------------------


def test_missing_series_raises() -> None:
    with pytest.raises(ChartDataError, match="series"):
        parse_chart_data({}, chart_type="bar")


def test_empty_series_raises() -> None:
    with pytest.raises(ChartDataError, match="series"):
        parse_chart_data({"series": []}, chart_type="bar")


def test_invalid_json_string_raises() -> None:
    with pytest.raises(ChartDataError):
        parse_chart_data("not-json", chart_type="bar")


def test_missing_chart_type_raises() -> None:
    source = {"series": [{"name": "A", "values": [1]}]}
    with pytest.raises(ChartDataError, match="chart_type"):
        parse_chart_data(source)


def test_invalid_chart_type_raises() -> None:
    with pytest.raises(ChartDataError, match="chart_type"):
        parse_chart_data({"series": [{"name": "A", "values": [1]}]}, chart_type="donut")


def test_series_missing_values_raises() -> None:
    source = {"series": [{"name": "A"}]}
    with pytest.raises(ChartDataError):
        parse_chart_data(source, chart_type="bar")


def test_series_non_numeric_values_raises() -> None:
    source = {"series": [{"name": "A", "values": ["x", "y"]}]}
    with pytest.raises(ChartDataError):
        parse_chart_data(source, chart_type="bar")
