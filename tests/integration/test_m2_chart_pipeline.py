"""Integration test — M2 chart rendering through the build pipeline (E2E)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aio.commands.build import build_pipeline


@pytest.fixture()
def chart_slide(tmp_path: Path) -> Path:
    """Create a slides.md with @chart-type/@chart-data metadata."""
    slides = tmp_path / "charts.md"
    chart_data = json.dumps(
        {
            "labels": ["Q1", "Q2", "Q3", "Q4"],
            "series": [{"name": "Revenue", "values": [10, 20, 15, 25]}],
        }
    )
    slides.write_text(
        f"""---
title: Chart Demo
theme: minimal
---

<!-- @layout: split-image-text -->
<!-- @title: Revenue Chart -->
<!-- @chart-type: bar -->
<!-- @chart-data: {chart_data} -->

A bar chart showing quarterly revenue.
""",
        encoding="utf-8",
    )
    return slides


def test_chart_build_produces_data_uri(tmp_path: Path, chart_slide: Path) -> None:
    """Build pipeline converts @chart-type/@chart-data to a data URI in output HTML."""
    out = tmp_path / "out.html"
    build_pipeline(chart_slide, output=out, theme_id="minimal")
    html = out.read_text(encoding="utf-8")
    assert "data:image/svg+xml" in html, "Expected chart data URI in output HTML"


def test_chart_build_svg_no_script(tmp_path: Path, chart_slide: Path) -> None:
    """Rendered chart SVG in output must not contain <script> tags."""
    out = tmp_path / "out.html"
    build_pipeline(chart_slide, output=out, theme_id="minimal")
    html = out.read_text(encoding="utf-8")
    # The encoded SVG should not contain %3Cscript (URL-encoded <script)
    assert "%3Cscript" not in html.lower()


def test_chart_build_invalid_data_falls_back_gracefully(tmp_path: Path) -> None:
    """Invalid @chart-data triggers a warning but build continues (no crash)."""
    slides = tmp_path / "bad_chart.md"
    slides.write_text(
        """---
title: Bad Chart
---

<!-- @layout: split-image-text -->
<!-- @chart-type: bar -->
<!-- @chart-data: this-is-not-json -->

Body text with no chart.
""",
        encoding="utf-8",
    )
    out = tmp_path / "out.html"
    # Should not raise — falls back gracefully
    build_pipeline(slides, output=out, theme_id="minimal")
    assert out.exists()


@pytest.mark.parametrize("chart_type", ["bar", "line", "pie", "scatter", "heatmap"])
def test_all_chart_types_produce_valid_html(tmp_path: Path, chart_type: str) -> None:
    """Each supported chart type produces a valid HTML output file."""
    chart_data = json.dumps(
        {
            "labels": ["A", "B", "C"],
            "series": [{"name": "S1", "values": [1, 2, 3]}],
        }
    )
    slides = tmp_path / f"chart_{chart_type}.md"
    slides.write_text(
        f"""---
title: {chart_type} test
---

<!-- @layout: split-image-text -->
<!-- @chart-type: {chart_type} -->
<!-- @chart-data: {chart_data} -->

Body.
""",
        encoding="utf-8",
    )
    out = tmp_path / f"out_{chart_type}.html"
    build_pipeline(slides, output=out, theme_id="minimal")
    assert out.exists()
    html = out.read_text(encoding="utf-8")
    assert "data:image/svg+xml" in html
