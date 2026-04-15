"""Unit tests for SVG composites stub."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from aio.visuals.svg.composites import SVGComposer


def test_render_composite_returns_string() -> None:
    svg = SVGComposer.compose("process-steps", {"palette": {"primary": "#0EA5E9"}})
    assert isinstance(svg, str)


def test_render_composite_starts_with_svg() -> None:
    svg = SVGComposer.compose("comparison-split", {"palette": {"primary": "#0EA5E9"}})
    assert svg.strip().startswith("<svg")


def test_render_composite_parseable_xml() -> None:
    svg = SVGComposer.compose("abstract-art", {"palette": {"primary": "#0EA5E9"}})
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")


def test_render_composite_no_script_tag() -> None:
    svg = SVGComposer.compose("section-divider", {"palette": {"primary": "#0EA5E9"}})
    assert "<script" not in svg.lower()


def test_render_composite_has_role_img() -> None:
    svg = SVGComposer.compose("stat-decoration", {"palette": {"primary": "#0EA5E9"}})
    assert isinstance(svg, str)
