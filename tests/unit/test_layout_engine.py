"""Tests for the Layout Template Engine and CompositionEngine (US3)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from aio.exceptions import LayoutNotFoundError
from aio.layouts import LAYOUT_REGISTRY, LayoutRecord

# ---------------------------------------------------------------------------
# Registry discovery tests
# ---------------------------------------------------------------------------


class TestLayoutRegistry:
    """LAYOUT_REGISTRY auto-discovers all .j2 files."""

    def test_all_16_layouts_discovered(self) -> None:
        assert len(LAYOUT_REGISTRY) == 16, (
            f"Expected 16 layouts, got {len(LAYOUT_REGISTRY)}: {list(LAYOUT_REGISTRY.keys())}"
        )

    def test_expected_layout_names_present(self) -> None:
        expected = {
            "hero-title", "content", "two-column", "three-column", "full-image",
            "code", "quote", "timeline", "comparison", "gallery", "data",
            "icon-grid", "narrative", "diagram", "custom", "interactive",
        }
        assert set(LAYOUT_REGISTRY.keys()) == expected

    def test_each_record_has_name_path_blocks(self) -> None:
        for name, record in LAYOUT_REGISTRY.items():
            assert isinstance(record, LayoutRecord)
            assert record.name == name
            assert record.path.endswith(".j2")
            assert isinstance(record.blocks, list)

    def test_hero_title_has_correct_blocks(self) -> None:
        record = LAYOUT_REGISTRY["hero-title"]
        assert "title" in record.blocks
        assert "subtitle" in record.blocks

    def test_content_layout_has_title_and_body(self) -> None:
        record = LAYOUT_REGISTRY["content"]
        assert "title" in record.blocks
        assert "body" in record.blocks

    def test_zero_block_layouts_load_without_error(self) -> None:
        # narrative, diagram, custom, interactive all have 1 block (content)
        for name in ("narrative", "diagram", "custom", "interactive"):
            record = LAYOUT_REGISTRY[name]
            assert isinstance(record.blocks, list)

    def test_blocks_list_has_no_duplicates(self) -> None:
        for name, record in LAYOUT_REGISTRY.items():
            assert len(record.blocks) == len(set(record.blocks)), (
                f"Layout '{name}' has duplicate blocks: {record.blocks}"
            )


# ---------------------------------------------------------------------------
# CompositionEngine tests
# ---------------------------------------------------------------------------


@dataclass
class _MockSlide:
    """Minimal slide object for testing."""

    index: int = 0
    metadata: dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


class TestCompositionEngineInferLayout:
    """CompositionEngine.infer_layout() resolves layout names."""

    def setup_method(self) -> None:
        from aio.composition.engine import CompositionEngine

        self.engine = CompositionEngine()

    def test_default_layout_is_content(self) -> None:
        slide = _MockSlide()
        assert self.engine.infer_layout(slide) == "content"

    def test_explicit_layout_override(self) -> None:
        slide = _MockSlide(metadata={"layout": "hero-title"})
        assert self.engine.infer_layout(slide) == "hero-title"

    def test_unknown_layout_raises_layout_not_found(self) -> None:
        slide = _MockSlide(metadata={"layout": "nonexistent-layout"})
        with pytest.raises(LayoutNotFoundError):
            self.engine.infer_layout(slide)

    def test_unknown_layout_includes_suggestion(self) -> None:
        # "content" is close to "contents"
        slide = _MockSlide(metadata={"layout": "contents"})
        with pytest.raises(LayoutNotFoundError) as exc_info:
            self.engine.infer_layout(slide)
        # suggestion should be non-None since "contents" is close to "content"
        assert exc_info.value.suggestion is not None

    def test_engine_loads_all_16_layouts(self) -> None:
        assert len(self.engine.layout_registry) == 16


class TestCompositionEngineRender:
    """CompositionEngine.render() produces correct HTML output."""

    def setup_method(self) -> None:
        from aio.composition.engine import CompositionEngine

        self.engine = CompositionEngine()

    def test_render_hero_title_with_context(self) -> None:
        slide = _MockSlide(metadata={"layout": "hero-title"})
        context = {"title": "Welcome", "subtitle": "To AIO"}
        result = self.engine.render(slide, "hero-title", context)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_unknown_layout_raises(self) -> None:
        slide = _MockSlide()
        with pytest.raises(LayoutNotFoundError):
            self.engine.render(slide, "nonexistent", {})

    def test_render_is_deterministic(self) -> None:
        slide = _MockSlide(metadata={"layout": "content"})
        context = {"title": "Deterministic", "body": "same output"}
        result1 = self.engine.render(slide, "content", context)
        result2 = self.engine.render(slide, "content", context)
        assert result1 == result2

    def test_render_all_16_layouts_without_error(self) -> None:
        slide = _MockSlide()
        for name in LAYOUT_REGISTRY:
            result = self.engine.render(slide, name, {})
            assert isinstance(result, str)


class TestLayoutInheritance:
    """Jinja2 inheritance works (extends/block override)."""

    def test_content_layout_renders_with_body_override(self) -> None:
        # The content layout has {% block body %} — render with a value
        from aio._tpl import make_jinja_env

        env = make_jinja_env()
        # Create an ad-hoc child template that extends content.j2
        child_src = (  # noqa: E501
            '{% extends "content.j2" %}'
            "{% block title %}My Title{% endblock %}"
            "{% block body %}My Body{% endblock %}"
        )
        tmpl = env.from_string(child_src)
        rendered = tmpl.render()
        assert "My Title" in rendered
        assert "My Body" in rendered
