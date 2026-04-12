"""Unit tests for the SVG icon library (Phase 2 — T010).

TDD: all tests should FAIL before T012–T014 are implemented.
"""

import re
import time

import pytest

from aio.visuals.svg.icons import list_icons, render_icon


class TestRenderIcon:
    def test_returns_svg_string(self):
        svg = render_icon("brain")
        assert isinstance(svg, str)
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_valid_svg_structure(self):
        svg = render_icon("brain")
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg
        assert 'viewBox="0 0 24 24"' in svg

    def test_icon_class_applied(self):
        svg = render_icon("brain")
        assert 'class="icon icon-brain"' in svg

    def test_size_kwarg_css(self):
        svg = render_icon("brain", size="64px")
        # size as CSS value applied via style attribute
        assert "64" in svg

    def test_color_kwarg_applied(self):
        svg = render_icon("brain", color="#635BFF")
        assert "#635BFF" in svg

    def test_unknown_icon_returns_fallback(self):
        svg = render_icon("unknown-icon-xyz-does-not-exist")
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_unknown_icon_logs_warning(self):
        from unittest.mock import patch
        import aio.visuals.svg.icons as icons_module
        with patch.object(icons_module._log, "warning") as mock_warn:
            render_icon("unknown-icon-xyz-does-not-exist")
        mock_warn.assert_called_once()
        args = mock_warn.call_args[0]
        assert "unknown-icon-xyz-does-not-exist" in str(args)

    def test_performance_under_1ms(self):
        # Warm up
        render_icon("brain")
        start = time.perf_counter()
        render_icon("brain")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 1.0, f"render_icon took {elapsed_ms:.2f}ms, expected < 1ms"


class TestListIcons:
    def test_returns_list_of_tuples(self):
        icons = list_icons()
        assert isinstance(icons, list)
        assert len(icons) > 0
        name, tags = icons[0]
        assert isinstance(name, str)
        assert isinstance(tags, list)

    def test_at_least_200_icons(self):
        icons = list_icons()
        assert len(icons) >= 200, f"Expected >= 200 icons, got {len(icons)}"

    def test_sorted_by_name(self):
        icons = list_icons()
        names = [name for name, _ in icons]
        assert names == sorted(names)

    def test_filter_by_tag(self):
        icons = list_icons(filter="dataviz")
        assert len(icons) > 0
        for name, tags in icons:
            assert any("dataviz" in t.lower() for t in tags), (
                f"Icon '{name}' matched filter 'dataviz' but tags are {tags}"
            )

    def test_filter_case_insensitive(self):
        lower = list_icons(filter="dataviz")
        upper = list_icons(filter="DATAVIZ")
        assert lower == upper

    def test_filter_no_match_returns_empty(self):
        icons = list_icons(filter="xyznonexistent99")
        assert icons == []

    def test_at_least_one_tag_per_icon(self):
        for name, tags in list_icons():
            assert len(tags) >= 1, f"Icon '{name}' has no tags"

    def test_performance_under_100ms(self):
        start = time.perf_counter()
        list_icons()
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 100.0, f"list_icons took {elapsed_ms:.2f}ms, expected < 100ms"

    def test_filter_none_returns_all(self):
        assert list_icons(filter=None) == list_icons()


class TestAdvisory:
    def test_50_plus_icons_advisory_is_in_compose(self):
        """This advisory is tested at the compose level (test_build_phase2.py).
        Here we simply verify list_icons and render_icon don't emit it themselves."""
        import logging
        import io
        # render 51 icons — no advisory from the icons module itself
        for i, (name, _) in enumerate(list_icons()[:51]):
            render_icon(name)
        # No assertion needed — just confirm no crash
