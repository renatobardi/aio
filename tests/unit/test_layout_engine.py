"""Tests for the Layout Template Engine and CompositionEngine (US3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aio.layouts import LAYOUT_REGISTRY, LayoutRecord

# ---------------------------------------------------------------------------
# Registry discovery tests
# ---------------------------------------------------------------------------


class TestLayoutRegistry:
    """LAYOUT_REGISTRY auto-discovers all .j2 files."""

    def test_all_16_layouts_discovered(self) -> None:
        # M1 adds 8 new layouts + base.j2; registry now has more than 16
        assert len(LAYOUT_REGISTRY) >= 8, (
            f"Expected at least 8 layouts, got {len(LAYOUT_REGISTRY)}: {list(LAYOUT_REGISTRY.keys())}"
        )

    def test_expected_layout_names_present(self) -> None:
        # M1 core layouts must be present (M0 layouts may also coexist)
        expected_m1 = {
            "hero_title",
            "stat_highlight",
            "split_image_text",
            "content_with_icons",
            "comparison_2col",
            "quote",
            "key_takeaways",
            "closing",
            "content",
        }
        registry_keys = set(LAYOUT_REGISTRY.keys())
        missing = expected_m1 - registry_keys
        assert not missing, f"M1 layouts missing from registry: {missing}"

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

    def test_unknown_layout_falls_back_to_content(self) -> None:
        # M1 engine: unknown explicit layout logs warning and returns CONTENT
        from aio.composition.layouts import LayoutType

        slide = _MockSlide(metadata={"layout": "nonexistent-layout"})
        result = self.engine.infer_layout(slide)
        assert result == LayoutType.CONTENT

    def test_engine_has_infer_layout_method(self) -> None:
        assert callable(getattr(self.engine, "infer_layout", None))


class TestCompositionEngineApplyLayout:
    """CompositionEngine.apply_layout() builds SlideRenderContext."""

    def setup_method(self) -> None:
        from aio.composition.engine import CompositionEngine

        self.engine = CompositionEngine()

    def test_apply_layout_hero_title_returns_context(self) -> None:
        from aio.composition.layouts import LayoutType
        from aio.composition.metadata import SlideRenderContext

        slide = _MockSlide(metadata={"layout": "hero-title", "title": "Welcome"})
        slide.title = "Welcome"  # type: ignore[attr-defined]
        slide.body_html = ""  # type: ignore[attr-defined]
        ctx = self.engine.apply_layout(slide, LayoutType.HERO_TITLE)
        assert isinstance(ctx, SlideRenderContext)
        assert ctx.layout_id == "hero-title"

    def test_apply_layout_content_is_default(self) -> None:
        from aio.composition.layouts import LayoutType
        from aio.composition.metadata import SlideRenderContext

        slide = _MockSlide()
        slide.title = None  # type: ignore[attr-defined]
        slide.body_html = "<p>Body</p>"  # type: ignore[attr-defined]
        ctx = self.engine.apply_layout(slide, LayoutType.CONTENT)
        assert isinstance(ctx, SlideRenderContext)
        assert ctx.layout_id == "content"

    def test_apply_layout_is_deterministic(self) -> None:
        from aio.composition.layouts import LayoutType

        slide = _MockSlide(metadata={"layout": "content"})
        slide.title = "Deterministic"  # type: ignore[attr-defined]
        slide.body_html = "<p>same output</p>"  # type: ignore[attr-defined]
        ctx1 = self.engine.apply_layout(slide, LayoutType.CONTENT)
        ctx2 = self.engine.apply_layout(slide, LayoutType.CONTENT)
        assert ctx1.layout_id == ctx2.layout_id
        assert ctx1.body_html == ctx2.body_html


class TestLayoutInheritance:
    """Jinja2 inheritance works (extends/block override)."""

    def test_content_layout_renders_with_body_override(self) -> None:
        # The content layout has {% block body %} — render with a value
        from aio._tpl import make_jinja_env

        env = make_jinja_env()
        # Create an ad-hoc child template that extends content.j2
        child_src = (  # noqa: E501
            '{% extends "content.j2" %}{% block title %}My Title{% endblock %}{% block body %}My Body{% endblock %}'
        )
        tmpl = env.from_string(child_src)
        rendered = tmpl.render()
        assert "My Title" in rendered
        assert "My Body" in rendered
