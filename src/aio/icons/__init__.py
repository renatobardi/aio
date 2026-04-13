"""AIO icon package — re-exports ICON_REGISTRY from visuals.svg.icons."""

from __future__ import annotations

from aio.visuals.svg.icons import ICON_REGISTRY, list_icons, render_icon

__all__ = ["ICON_REGISTRY", "list_icons", "render_icon"]
