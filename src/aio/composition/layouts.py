"""
LayoutType enum and per-layout SlotSpec definitions.
Maps layout IDs to their required/optional context fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class LayoutType(StrEnum):
    HERO_TITLE = "hero-title"
    STAT_HIGHLIGHT = "stat-highlight"
    SPLIT_IMAGE_TEXT = "split-image-text"
    CONTENT_WITH_ICONS = "content-with-icons"
    COMPARISON_2COL = "comparison-2col"
    QUOTE = "quote"
    KEY_TAKEAWAYS = "key-takeaways"
    CLOSING = "closing"
    CONTENT = "content"

    @classmethod
    def from_string(cls, value: str) -> LayoutType:
        """Case-insensitive lookup; returns CONTENT for unknown values."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.CONTENT


@dataclass(frozen=True)
class SlotSpec:
    """Describes the context fields a layout requires and accepts."""

    required: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)


LAYOUT_SLOTS: dict[LayoutType, SlotSpec] = {
    LayoutType.HERO_TITLE: SlotSpec(
        required=[],
        optional=["title", "body_html", "speaker_notes"],
    ),
    LayoutType.STAT_HIGHLIGHT: SlotSpec(
        required=["stat_value"],
        optional=["stat_label", "stat_description", "speaker_notes"],
    ),
    LayoutType.SPLIT_IMAGE_TEXT: SlotSpec(
        required=[],
        optional=["title", "body_html", "image_src", "image_alt", "image_position", "speaker_notes"],
    ),
    LayoutType.CONTENT_WITH_ICONS: SlotSpec(
        required=[],
        optional=["title", "body_html", "speaker_notes"],
    ),
    LayoutType.COMPARISON_2COL: SlotSpec(
        required=[],
        optional=["left_title", "left_content", "right_title", "right_content", "speaker_notes"],
    ),
    LayoutType.QUOTE: SlotSpec(
        required=[],
        optional=["quote_text", "quote_attribution", "speaker_notes"],
    ),
    LayoutType.KEY_TAKEAWAYS: SlotSpec(
        required=[],
        optional=["title", "body_html", "speaker_notes"],
    ),
    LayoutType.CLOSING: SlotSpec(
        required=[],
        optional=["title", "body_html", "cta_text", "speaker_notes"],
    ),
    LayoutType.CONTENT: SlotSpec(
        required=[],
        optional=["title", "body_html", "speaker_notes"],
    ),
}
