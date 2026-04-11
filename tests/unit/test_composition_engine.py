"""Unit tests for CompositionEngine.infer_layout() — 9-rule priority chain (T014)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from aio.composition.engine import CompositionEngine
from aio.composition.layouts import LayoutType


@dataclass
class _FakeSlide:
    index: int = 0
    metadata: dict[str, str] = field(default_factory=dict)
    raw_markdown: str = ""
    title: str | None = None
    body_html: str = ""


engine = CompositionEngine()


# ---------------------------------------------------------------------------
# Rule 1 — explicit @layout metadata
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("layout_str,expected", [
    ("hero-title", LayoutType.HERO_TITLE),
    ("stat-highlight", LayoutType.STAT_HIGHLIGHT),
    ("split-image-text", LayoutType.SPLIT_IMAGE_TEXT),
    ("content-with-icons", LayoutType.CONTENT_WITH_ICONS),
    ("comparison-2col", LayoutType.COMPARISON_2COL),
    ("quote", LayoutType.QUOTE),
    ("key-takeaways", LayoutType.KEY_TAKEAWAYS),
    ("closing", LayoutType.CLOSING),
    ("content", LayoutType.CONTENT),
])
def test_explicit_layout_honoured(layout_str: str, expected: LayoutType) -> None:
    slide = _FakeSlide(metadata={"layout": layout_str})
    assert engine.infer_layout(slide) == expected


def test_unknown_explicit_layout_falls_back_to_content() -> None:
    slide = _FakeSlide(metadata={"layout": "galaxy-brain"})
    assert engine.infer_layout(slide) == LayoutType.CONTENT


def test_auto_layout_triggers_inference() -> None:
    slide = _FakeSlide(metadata={"layout": "auto"}, raw_markdown="Plain text with no special markers.")
    assert engine.infer_layout(slide) == LayoutType.CONTENT


# ---------------------------------------------------------------------------
# Rule 2 — stat metadata
# ---------------------------------------------------------------------------

def test_infer_stat_from_metadata() -> None:
    slide = _FakeSlide(metadata={"stat": "87%", "label": "Accuracy"})
    assert engine.infer_layout(slide) == LayoutType.STAT_HIGHLIGHT


def test_infer_stat_with_description_only() -> None:
    slide = _FakeSlide(metadata={"stat": "1.2M", "description": "Users served"})
    assert engine.infer_layout(slide) == LayoutType.STAT_HIGHLIGHT


# ---------------------------------------------------------------------------
# Rule 3 — quote metadata
# ---------------------------------------------------------------------------

def test_infer_quote_from_metadata() -> None:
    slide = _FakeSlide(metadata={"quote": "Innovation is saying no."})
    assert engine.infer_layout(slide) == LayoutType.QUOTE


# ---------------------------------------------------------------------------
# Rule 4 — image metadata
# ---------------------------------------------------------------------------

def test_infer_split_image_from_metadata() -> None:
    slide = _FakeSlide(metadata={"image": "/assets/diagram.png"})
    assert engine.infer_layout(slide) == LayoutType.SPLIT_IMAGE_TEXT


# ---------------------------------------------------------------------------
# Rule 5 — comparison metadata
# ---------------------------------------------------------------------------

def test_infer_comparison_from_left_title() -> None:
    slide = _FakeSlide(metadata={"left-title": "Option A", "right-title": "Option B"})
    assert engine.infer_layout(slide) == LayoutType.COMPARISON_2COL


# ---------------------------------------------------------------------------
# Rule 6 — CTA metadata
# ---------------------------------------------------------------------------

def test_infer_closing_from_cta() -> None:
    slide = _FakeSlide(metadata={"cta": "Get started with aio init"})
    assert engine.infer_layout(slide) == LayoutType.CLOSING


# ---------------------------------------------------------------------------
# Rule 7 — body stat pattern
# ---------------------------------------------------------------------------

def test_infer_stat_from_body_percentage() -> None:
    slide = _FakeSlide(raw_markdown="We achieved **98% uptime** last quarter across all regions.")
    assert engine.infer_layout(slide) == LayoutType.STAT_HIGHLIGHT


# ---------------------------------------------------------------------------
# Rule 8 — list body
# ---------------------------------------------------------------------------

def test_infer_key_takeaways_from_list_body() -> None:
    slide = _FakeSlide(raw_markdown="- Item one\n- Item two\n- Item three\n- Item four")
    assert engine.infer_layout(slide) == LayoutType.KEY_TAKEAWAYS


def test_short_list_does_not_trigger_key_takeaways() -> None:
    slide = _FakeSlide(raw_markdown="- Item one\n- Item two")
    # Only 2 items — should not trigger KEY_TAKEAWAYS
    result = engine.infer_layout(slide)
    assert result != LayoutType.KEY_TAKEAWAYS


# ---------------------------------------------------------------------------
# Rule 9 — default fallback
# ---------------------------------------------------------------------------

def test_default_fallback_is_content() -> None:
    slide = _FakeSlide(raw_markdown="Just some plain narrative text with no special markers.")
    assert engine.infer_layout(slide) == LayoutType.CONTENT
