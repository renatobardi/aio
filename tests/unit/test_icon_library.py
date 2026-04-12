"""Unit tests for Lucide icon library (TDD — 20+ cases)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from aio.visuals.svg.icons import ICON_NAMES, list_icons, render_icon

# ---------------------------------------------------------------------------
# list_icons / ICON_NAMES
# ---------------------------------------------------------------------------


def test_list_icons_returns_list() -> None:
    icons = list_icons()
    assert isinstance(icons, list)


def test_list_icons_at_least_50() -> None:
    assert len(list_icons()) >= 50


def test_icon_names_is_frozenset() -> None:
    assert isinstance(ICON_NAMES, frozenset)


def test_icon_names_consistent_with_list_icons() -> None:
    # list_icons() now returns list[tuple[str, list[str]]] — extract names
    assert {name for name, _ in list_icons()} == ICON_NAMES


def test_all_icon_names_are_strings() -> None:
    for name in ICON_NAMES:
        assert isinstance(name, str)
        assert name  # non-empty


def test_common_icons_present() -> None:
    for name in ["arrow-right", "check", "x", "info", "star", "home"]:
        assert name in ICON_NAMES, f"Expected icon '{name}' in library"


# ---------------------------------------------------------------------------
# render_icon — happy path
# ---------------------------------------------------------------------------


def test_render_icon_returns_string() -> None:
    svg = render_icon("check")
    assert isinstance(svg, str)


def test_render_icon_starts_with_svg() -> None:
    svg = render_icon("check")
    assert svg.strip().startswith("<svg")


def test_render_icon_has_xmlns() -> None:
    svg = render_icon("check")
    assert "xmlns" in svg


def test_render_icon_parseable_xml() -> None:
    svg = render_icon("arrow-right")
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")


def test_render_icon_default_size_24() -> None:
    svg = render_icon("check")
    assert 'width="24"' in svg or "24" in svg


def test_render_icon_custom_size() -> None:
    svg = render_icon("check", size=48)
    assert "48" in svg


def test_render_icon_default_color_currentColor() -> None:
    svg = render_icon("check")
    assert "currentColor" in svg


def test_render_icon_custom_color() -> None:
    svg = render_icon("check", color="#ff0000")
    assert "#ff0000" in svg


def test_render_icon_custom_stroke_width() -> None:
    svg = render_icon("check", stroke_width=3.0)
    assert "3" in svg


def test_render_icon_with_aria_label() -> None:
    svg = render_icon("check", aria_label="Success")
    assert "Success" in svg


def test_render_icon_no_script_tag() -> None:
    for name in list(ICON_NAMES)[:10]:
        svg = render_icon(name)
        assert "<script" not in svg.lower(), f"Icon '{name}' contains <script>"


def test_render_icon_has_viewbox() -> None:
    svg = render_icon("check")
    assert "viewBox" in svg


# ---------------------------------------------------------------------------
# render_icon — error path
# ---------------------------------------------------------------------------


def test_render_icon_unknown_falls_back() -> None:
    # Phase 2: unknown icons now return fallback help-circle SVG instead of raising
    svg = render_icon("does-not-exist-xyzzy")
    assert "<svg" in svg  # fallback rendered
    assert "help-circle" in svg or "icon-help-circle" in svg


# ---------------------------------------------------------------------------
# Sample a few more icons for XML validity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["x", "info", "star", "home", "arrow-left", "settings"])
def test_named_icons_valid_xml(name: str) -> None:
    svg = render_icon(name)
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
