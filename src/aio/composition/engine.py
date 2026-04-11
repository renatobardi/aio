"""
CompositionEngine: layout inference and slide context construction.
Every slide passes through infer_layout() before rendering (Art. III).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

from aio._log import get_logger
from aio.composition.layouts import LAYOUT_SLOTS, LayoutType
from aio.composition.metadata import SlideRenderContext
from aio.exceptions import SlideContextError

_log = get_logger(__name__)

# Inference heuristic patterns (research.md §5 priority chain)
_STAT_RE = re.compile(r"\b\d+[\.,]?\d*\s*%|\b\d{1,3}[kKmMbB]\b|\b\d+\s*(ms|fps|px|rpm)\b")
_LIST_MIN_ITEMS = 3


class CompositionEngine:
    """Stateless after construction — thread-safe for concurrent renders."""

    def infer_layout(self, slide: Any) -> LayoutType:
        """
        9-rule priority chain for automatic layout detection.

        Priority (highest → lowest):
          1. Explicit @layout tag (not 'auto') → honour it
          2. Both @stat and (@label or @description) present → STAT_HIGHLIGHT
          3. @quote present → QUOTE
          4. @image present → SPLIT_IMAGE_TEXT
          5. @left-title or @right-title present → COMPARISON_2COL
          6. @cta present → CLOSING
          7. Body contains a prominent stat pattern (number + %) → STAT_HIGHLIGHT
          8. Body is a list with >= 3 items → KEY_TAKEAWAYS
          9. Default fallback → CONTENT
        """
        metadata: dict[str, str] = getattr(slide, "metadata", {})
        body: str = getattr(slide, "raw_markdown", "") or ""

        # Rule 1 — explicit @layout tag
        explicit = metadata.get("layout", "").strip()
        if explicit and explicit != "auto":
            layout = LayoutType.from_string(explicit)
            if layout == LayoutType.CONTENT and explicit not in ("content", ""):
                _log.warning("Unknown explicit layout '%s' — falling back to 'content'", explicit)
            else:
                _log.debug("Explicit layout '%s' for slide %s", layout.value, getattr(slide, "index", "?"))
            return layout

        # Rule 2 — stat metadata
        if "stat" in metadata and ("label" in metadata or "description" in metadata):
            _log.debug("Inferred STAT_HIGHLIGHT (metadata) for slide %s", getattr(slide, "index", "?"))
            return LayoutType.STAT_HIGHLIGHT

        # Rule 3 — quote metadata
        if "quote" in metadata:
            _log.debug("Inferred QUOTE (metadata) for slide %s", getattr(slide, "index", "?"))
            return LayoutType.QUOTE

        # Rule 4 — image metadata
        if "image" in metadata:
            _log.debug("Inferred SPLIT_IMAGE_TEXT (metadata) for slide %s", getattr(slide, "index", "?"))
            return LayoutType.SPLIT_IMAGE_TEXT

        # Rule 5 — comparison metadata
        if "left-title" in metadata or "right-title" in metadata:
            _log.debug("Inferred COMPARISON_2COL (metadata) for slide %s", getattr(slide, "index", "?"))
            return LayoutType.COMPARISON_2COL

        # Rule 6 — CTA / closing metadata
        if "cta" in metadata:
            _log.debug("Inferred CLOSING (metadata) for slide %s", getattr(slide, "index", "?"))
            return LayoutType.CLOSING

        # Rule 7 — body stat pattern
        if _STAT_RE.search(body):
            _log.debug("Inferred STAT_HIGHLIGHT (body pattern) for slide %s", getattr(slide, "index", "?"))
            return LayoutType.STAT_HIGHLIGHT

        # Rule 8 — list body
        list_items = re.findall(r"^[-*+]\s", body, re.MULTILINE)
        if len(list_items) >= _LIST_MIN_ITEMS:
            _log.debug("Inferred KEY_TAKEAWAYS (list body) for slide %s", getattr(slide, "index", "?"))
            return LayoutType.KEY_TAKEAWAYS

        # Rule 9 — default
        return LayoutType.CONTENT

    def apply_layout(self, slide: Any, layout_type: LayoutType) -> SlideRenderContext:
        """Build a SlideRenderContext from a SlideAST and resolved LayoutType."""
        metadata: dict[str, str] = getattr(slide, "metadata", {})
        index: int = getattr(slide, "index", 0)
        title: str | None = getattr(slide, "title", None) or metadata.get("title")
        body_html: str = getattr(slide, "body_html", "") or ""

        ctx = SlideRenderContext(
            slide_index=index,
            slide_id=f"slide-{index}",
            layout_id=layout_type.value,
            is_inferred=(metadata.get("layout", "auto") in ("", "auto")),
            title=title,
            body_html=body_html,
            speaker_notes=metadata.get("notes"),
            stat_value=metadata.get("stat"),
            stat_label=metadata.get("label"),
            stat_description=metadata.get("description"),
            quote_text=metadata.get("quote"),
            quote_attribution=metadata.get("author"),
            image_alt=metadata.get("alt"),
            image_position=metadata.get("image-position", "right"),
            cta_text=metadata.get("cta"),
            left_title=metadata.get("left-title"),
            left_content=metadata.get("left-content"),
            right_title=metadata.get("right-title"),
            right_content=metadata.get("right-content"),
        )

        # Validate required fields for chosen layout
        slot = LAYOUT_SLOTS.get(layout_type)
        if slot:
            for required_field in slot.required:
                if not getattr(ctx, required_field, None):
                    raise SlideContextError(layout_type.value, required_field)

        return ctx

    @staticmethod
    def sanitize_svg(svg_text: str) -> str:
        """
        Strip <script> tags and dangerous event attributes from SVG.
        Constitution Rule 7 — SVG output must not contain <script> tags.
        """
        try:
            root = ET.fromstring(svg_text)
        except ET.ParseError:
            _log.warning("SVG sanitization: could not parse SVG, returning empty string")
            return ""

        dangerous_attrs = {
            "onload", "onerror", "onclick", "onmouseover", "onmouseout",
            "onfocus", "onblur", "onchange", "onsubmit",
        }
        parent_map: dict[ET.Element, ET.Element] = {
            c: p for p in root.iter() for c in p
        }

        for elem in list(root.iter()):
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag.lower() == "script":
                parent = parent_map.get(elem)
                if parent is not None:
                    parent.remove(elem)
                continue

            for attr in list(elem.attrib.keys()):
                local = attr.split("}")[-1].lower()
                val = elem.attrib.get(attr, "")
                if local in dangerous_attrs or val.strip().lower().startswith("javascript:"):
                    del elem.attrib[attr]

        ET.register_namespace("", "http://www.w3.org/2000/svg")
        return ET.tostring(root, encoding="unicode")
