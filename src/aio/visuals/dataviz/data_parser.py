"""DataViz data model and parser — ChartData, Series, parse_chart_data()."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from aio.exceptions import ChartDataError

_VALID_CHART_TYPES: frozenset[str] = frozenset(
    {"bar", "line", "pie", "scatter", "heatmap", "donut", "sparkline", "timeline"}
)

# Regex for "Label:Value, Label:Value" inline syntax
_KV_RE = re.compile(r"([^:,\n]+):\s*([^,\n]+)")
# Regex for flat numeric CSV "10, 25, 18"
_NUMERIC_CSV_RE = re.compile(r"^[\d\s.,\-eE]+$")


@dataclass
class Series:
    """A single data series within a chart."""

    name: str
    values: list[float]
    color: str | None = None


@dataclass
class ChartData:
    """Parsed chart specification ready for rendering."""

    chart_type: Literal["bar", "line", "pie", "scatter", "heatmap", "donut", "sparkline", "timeline"]
    series: list[Series]
    labels: list[str] = field(default_factory=list)
    title: str | None = None
    width: int = 800
    height: int = 450


def _parse_inline_kv(source: str) -> tuple[list[str], list[float]]:
    """Parse 'Label:Value, Label:Value' inline CSV into (labels, values)."""
    labels: list[str] = []
    values: list[float] = []
    for m in _KV_RE.finditer(source):
        label = m.group(1).strip()
        try:
            val = float(m.group(2).strip())
        except ValueError:
            continue
        labels.append(label)
        values.append(val)
    return labels, values


def _parse_inline_numeric(source: str) -> list[float]:
    """Parse flat numeric CSV '10, 25, 18' into list of floats."""
    values: list[float] = []
    for token in re.split(r"[,\s]+", source.strip()):
        token = token.strip()
        if token:
            try:
                values.append(float(token))
            except ValueError:
                pass
    return values


def _parse_inline_timeline(source: str) -> list[tuple[str, str]]:
    """Parse multi-line 'date: event' pairs. Returns list of (date, event)."""
    pairs: list[tuple[str, str]] = []
    for line in source.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        colon_idx = line.find(":")
        if colon_idx == -1:
            pairs.append(("", line))
            continue
        date_part = line[:colon_idx].strip()
        event_part = line[colon_idx + 1 :].strip()
        pairs.append((date_part, event_part))
    return pairs


def parse_chart_data(
    source: str | dict[str, Any],
    chart_type: str | None = None,
    title: str | None = None,
) -> ChartData:
    """Parse inline string or JSON/dict into a ChartData object.

    Accepts three inline string formats (when chart_type is provided):
    - ``"Q1:50, Q2:75"`` — label:value CSV (bar, donut, line, pie)
    - ``"10, 25, 18"`` — flat numeric CSV (sparkline)
    - ``"2020-01: Alpha\\n2021-06: Beta"`` — multi-line date:event (timeline)

    Falls back to JSON parsing if the string looks like JSON.

    Args:
        source: Inline string, JSON string, or dict with chart specification.
        chart_type: Chart type (required for inline string formats).
        title: Title override.

    Returns:
        Populated ChartData.

    Raises:
        ChartDataError: On missing/invalid fields (logs warning and returns empty ChartData
                        for malformed inline input rather than raising).
    """
    import logging

    _log = logging.getLogger(__name__)

    resolved_type = chart_type

    # Handle inline string formats
    if isinstance(source, str) and resolved_type:
        stripped = source.strip()

        if resolved_type == "timeline":
            pairs = _parse_inline_timeline(stripped)
            if not pairs:
                _log.warning("Empty or malformed @data for timeline chart — rendering empty state")
                return ChartData(chart_type="timeline", series=[], labels=[])
            # Store events as series with label=date, name=event
            series = [Series(name=event, values=[0.0], color=None) for _, event in pairs]
            labels = [date for date, _ in pairs]
            return ChartData(chart_type="timeline", series=series, labels=labels, title=title)

        if resolved_type == "sparkline" or (_NUMERIC_CSV_RE.match(stripped) and ":" not in stripped):
            values = _parse_inline_numeric(stripped)
            if not values:
                _log.warning("Empty or malformed @data for sparkline — rendering empty state")
                return ChartData(chart_type=resolved_type, series=[], labels=[])  # type: ignore[arg-type]
            return ChartData(
                chart_type=resolved_type,  # type: ignore[arg-type]
                series=[Series(name="data", values=values)],
                labels=[],
                title=title,
            )

        # Try key:value CSV
        if ":" in stripped and not stripped.startswith("{"):
            labels, values = _parse_inline_kv(stripped)
            if labels and values:
                return ChartData(
                    chart_type=resolved_type,  # type: ignore[arg-type]
                    series=[Series(name="data", values=values)],
                    labels=labels,
                    title=title,
                )
            _log.warning("Malformed @data '%s' for %s chart — rendering empty state", stripped[:40], resolved_type)
            return ChartData(chart_type=resolved_type, series=[], labels=[], title=title)  # type: ignore[arg-type]

    # Fall back to JSON/dict parsing
    if isinstance(source, str):
        try:
            data: dict[str, Any] = json.loads(source)
        except json.JSONDecodeError as exc:
            raise ChartDataError(f"Invalid JSON: {exc}") from exc
    else:
        data = source

    # Resolve chart_type from data dict if not given
    if not resolved_type:
        resolved_type = data.get("chart_type")
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

    series_list: list[Series] = []
    for i, item in enumerate(raw_series):
        if "values" not in item:
            raise ChartDataError(f"series[{i}] missing 'values'", chart_type=resolved_type)
        try:
            values = [float(v) for v in item["values"]]
        except (TypeError, ValueError) as exc:
            raise ChartDataError(f"series[{i}] contains non-numeric values: {exc}", chart_type=resolved_type) from exc
        series_list.append(
            Series(
                name=str(item.get("name", f"Series {i + 1}")),
                values=values,
                color=item.get("color") or None,
            )
        )

    resolved_title = title if title is not None else data.get("title")

    return ChartData(
        chart_type=resolved_type,  # type: ignore[arg-type]
        series=series_list,
        labels=[str(label) for label in data.get("labels", [])],
        title=resolved_title or None,
        width=int(data.get("width", 800)),
        height=int(data.get("height", 450)),
    )
