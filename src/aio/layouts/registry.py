"""
LayoutTemplate and LayoutRegistry — importlib.resources discovery (Art. XII).
Works in pip, editable, zipapp, and PyInstaller distribution modes.
"""

from __future__ import annotations

import importlib.resources
import re
from dataclasses import dataclass
from pathlib import Path

from aio._log import get_logger
from aio.exceptions import LayoutDefinitionError, LayoutNotFoundError, LayoutRegistryError

_log = get_logger(__name__)

_BLOCK_RE = re.compile(r"\{%-?\s*block\s+([a-z_]+)\s*-?%\}")


@dataclass(frozen=True)
class LayoutTemplate:
    layout_id: str
    path: Path
    supported_blocks: list[str]
    description: str
    is_fallback: bool

    def __hash__(self) -> int:
        return hash(self.layout_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LayoutTemplate):
            return NotImplemented
        return self.layout_id == other.layout_id


class LayoutRegistry:
    """Lazy singleton registry — loaded once per process via LayoutRegistry.get()."""

    _instance: LayoutRegistry | None = None

    def __init__(self) -> None:
        self._layouts: dict[str, LayoutTemplate] = {}
        self._loaded: bool = False

    @classmethod
    def get(cls) -> LayoutRegistry:
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._discover()
        return cls._instance

    @classmethod
    def _reset(cls) -> None:
        """Reset singleton — used in tests only."""
        cls._instance = None

    def lookup(self, layout_id: str) -> LayoutTemplate:
        if layout_id not in self._layouts:
            raise LayoutNotFoundError(layout_id)
        return self._layouts[layout_id]

    def all_ids(self) -> list[str]:
        return sorted(self._layouts.keys())

    def fallback(self) -> LayoutTemplate:
        for tmpl in self._layouts.values():
            if tmpl.is_fallback:
                return tmpl
        raise LayoutRegistryError("No fallback layout registered.")

    def _discover(self) -> None:
        pkg = importlib.resources.files("aio.layouts")
        found: list[LayoutTemplate] = []

        for resource in pkg.iterdir():
            name = resource.name
            if not name.endswith(".j2") or name == "base.j2":
                continue

            path = Path(str(resource))
            try:
                source = resource.read_text(encoding="utf-8")
            except Exception as exc:
                raise LayoutDefinitionError(f"Cannot read layout '{name}': {exc}") from exc

            stem = name[:-3]  # strip .j2
            layout_id = re.sub(r"[^a-z0-9-]", "-", stem.lower())
            blocks = _BLOCK_RE.findall(source)
            description = _extract_description(source)
            is_fallback = layout_id == "content"

            found.append(
                LayoutTemplate(
                    layout_id=layout_id,
                    path=path,
                    supported_blocks=blocks if blocks else ["slide_content"],
                    description=description,
                    is_fallback=is_fallback,
                )
            )

        if not found:
            raise LayoutRegistryError("No .j2 layout templates found in aio.layouts package.")

        fallback_count = sum(1 for t in found if t.is_fallback)
        if fallback_count == 0:
            raise LayoutRegistryError("No fallback layout ('content.j2') found in registry.")

        self._layouts = {t.layout_id: t for t in found}
        self._loaded = True
        _log.debug("LayoutRegistry loaded %d layouts: %s", len(self._layouts), self.all_ids())


def _extract_description(source: str) -> str:
    """Extract the first Jinja2 comment block as the layout description."""
    # \s* removed from around .*? to eliminate ambiguous backtracking; result is .strip()ped below
    match = re.search(r"\{#-?(.*?)-?#\}", source, re.DOTALL)
    if match:
        first_line = match.group(1).strip().splitlines()[0].strip()
        return first_line
    return ""
