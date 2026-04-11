"""Theme path resolution and registry loading via importlib.resources."""
from __future__ import annotations

import importlib.resources
import json
from pathlib import Path

from aio._log import get_logger

_log = get_logger(__name__)


def load_registry() -> list[dict[str, str]]:
    """Load the global theme registry from src/aio/themes/registry.json."""
    data = (
        importlib.resources.files("aio.themes")
        .joinpath("registry.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(data)  # type: ignore[no-any-return]


def resolve_theme_path(theme_id: str) -> Path:
    """
    Return the filesystem path to a theme directory.

    Uses importlib.resources — works in pip and development modes.
    For zipapp/PyInstaller, callers should use files() API directly.
    """
    ref = importlib.resources.files("aio.themes") / theme_id
    return Path(str(ref))
