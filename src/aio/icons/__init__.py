"""AIO icon package — re-exports ICON_REGISTRY from visuals.svg.icons."""

from __future__ import annotations

from aio.visuals.svg.icons import _ICON_PATHS, _ICON_TAGS, list_icons, render_icon

ICON_REGISTRY: dict[str, dict[str, object]] = {
    name: {
        "id": name,
        "name": name.replace("-", " ").title(),
        "tags": _ICON_TAGS.get(name, []),
        "viewBox": "0 0 24 24",
        "path_data": path_data,
    }
    for name, path_data in _ICON_PATHS.items()
}

__all__ = ["ICON_REGISTRY", "list_icons", "render_icon"]
