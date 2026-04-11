"""
CompositionEngine: stateless layout inference and rendering.
Every slide passes through infer_layout() before rendering (Art. III).
"""
from __future__ import annotations

import difflib
from typing import Any

import jinja2

from aio._log import get_logger
from aio.exceptions import LayoutNotFoundError
from aio.layouts import LAYOUT_REGISTRY, LayoutRecord

_log = get_logger(__name__)


class CompositionEngine:
    """
    Stateless after construction — thread-safe for concurrent renders.
    Loads the layout registry once at __init__ time.
    """

    def __init__(self) -> None:
        self.layout_registry: dict[str, LayoutRecord] = dict(LAYOUT_REGISTRY)
        _log.debug(
            "CompositionEngine initialized with %d layouts: %s",
            len(self.layout_registry),
            list(self.layout_registry.keys()),
        )

    def _suggest(self, name: str) -> str | None:
        matches = difflib.get_close_matches(
            name, list(self.layout_registry.keys()), n=1, cutoff=0.6
        )
        return matches[0] if matches else None

    def infer_layout(self, slide: Any) -> str:
        """
        Return the layout name for the given slide.

        Priority:
          1. slide.metadata.get("layout") — explicit @layout override
          2. Heuristic (M0 stub: returns "content")

        Raises LayoutNotFoundError if the resolved name is not in the registry.
        """
        metadata = getattr(slide, "metadata", {})
        layout_name: str = metadata.get("layout", "content")
        if layout_name not in self.layout_registry:
            raise LayoutNotFoundError(layout_name, self._suggest(layout_name))
        _log.debug("Inferred layout '%s' for slide index %s", layout_name, getattr(slide, "index", "?"))
        return layout_name

    def render(self, slide: Any, layout_name: str, context: dict[str, Any]) -> str:
        """
        Render a slide using the named layout template.

        Returns an HTML string.
        Raises LayoutNotFoundError if layout_name not in registry.
        Raises jinja2.TemplateError on render failure.
        """
        if layout_name not in self.layout_registry:
            raise LayoutNotFoundError(layout_name, self._suggest(layout_name))

        from aio._tpl import make_jinja_env

        env = make_jinja_env()
        template_file = f"{layout_name}.j2"
        try:
            template = env.get_template(template_file)
            result = template.render(**context)
            _log.debug("Rendered layout '%s' (%d chars)", layout_name, len(result))
            return result
        except jinja2.TemplateError as exc:
            _log.error("Template render error for layout '%s': %s", layout_name, exc)
            raise
