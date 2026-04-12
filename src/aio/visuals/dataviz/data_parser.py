"""DataViz data model and parser — ChartData, Series, parse_chart_data()."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from aio.exceptions import ChartDataError

_VALID_CHART_TYPES: frozenset[str] = frozenset({"bar", "line", "pie", "scatter", "heatmap"})


@dataclass
class Series:
    """A single data series within a chart."""

    name: str
    values: list[float]
    color: str | None = None


@dataclass
class ChartData:
    """Parsed chart specification ready for rendering."""

    chart_type: Literal["bar", "line", "pie", "scatter", "heatmap"]
    series: list[Series]
    labels: list[str] = field(default_factory=list)
    title: str | None = None
    width: int = 800
    height: int = 450


def parse_chart_data(
    source: str | dict[str, Any],
    chart_type: str | None = None,
    title: str | None = None,
) -> ChartData:
    """Parse a JSON string or dict into a ChartData object.

    Args:
        source: JSON string or dict with chart specification.
        chart_type: Chart type override. Falls back to ``source["chart_type"]``.
        title: Title override. Falls back to ``source["title"]``.

    Returns:
        Populated ChartData.

    Raises:
        ChartDataError: On missing/invalid fields.
    """
    if isinstance(source, str):
        try:
            data: dict[str, Any] = json.loads(source)
        except json.JSONDecodeError as exc:
            raise ChartDataError(f"Invalid JSON: {exc}") from exc
    else:
        data = source

    # Resolve chart_type
    resolved_type = chart_type or data.get("chart_type")
    if not resolved_type:
        raise ChartDataError("chart_type is required (pass via kwarg or source['chart_type'])")
    if resolved_type not in _VALID_CHART_TYPES:
        raise ChartDataError(
            f"chart_type '{resolved_type}' is not valid. Must be one of: {sorted(_VALID_CHART_TYPES)}",
            chart_type=resolved_type,
        )

    # Parse series
    raw_series = data.get("series")
    if not raw_series:
        raise ChartDataError("series is required and must be non-empty", chart_type=resolved_type)

    series: list[Series] = []
    for i, item in enumerate(raw_series):
        if "values" not in item:
            raise ChartDataError(
                f"series[{i}] missing 'values'", chart_type=resolved_type
            )
        try:
            values = [float(v) for v in item["values"]]
        except (TypeError, ValueError) as exc:
            raise ChartDataError(
                f"series[{i}] contains non-numeric values: {exc}", chart_type=resolved_type
            ) from exc
        series.append(
            Series(
                name=str(item.get("name", f"Series {i + 1}")),
                values=values,
                color=item.get("color") or None,
            )
        )

    # Resolve title (kwarg takes priority)
    resolved_title = title if title is not None else data.get("title")

    return ChartData(
        chart_type=resolved_type,  # type: ignore[arg-type]
        series=series,
        labels=[str(label) for label in data.get("labels", [])],
        title=resolved_title or None,
        width=int(data.get("width", 800)),
        height=int(data.get("height", 450)),
    )
