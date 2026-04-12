"""Unit tests for SVG composites stub."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from aio.visuals.svg.composites import render_composite


def test_render_composite_returns_string() -> None:
    svg = render_composite("process-flow")
    assert isinstance(svg, str)


def test_render_composite_starts_with_svg() -> None:
    svg = render_composite("org-chart")
    assert svg.strip().startswith("<svg")


def test_render_composite_parseable_xml() -> None:
    svg = render_composite("timeline")
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")


def test_render_composite_no_script_tag() -> None:
    svg = render_composite("any-type")
    assert "<script" not in svg.lower()


def test_render_composite_has_role_img() -> None:
    svg = render_composite("timeline")
    assert 'role="img"' in svg
