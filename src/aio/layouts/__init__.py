"""
Auto-discover all .j2 layout templates at import time using importlib.resources.
Works in pip, zipapp, and PyInstaller distribution modes (Art. XII).
"""

from __future__ import annotations

import importlib.resources
import logging
import re
from dataclasses import dataclass, field

_log = logging.getLogger("aio.layouts")


@dataclass(frozen=True)
class LayoutRecord:
    name: str
    path: str
    blocks: list[str] = field(default_factory=list)

    def __hash__(self) -> int:
        return hash((self.name, self.path))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LayoutRecord):
            return NotImplemented
        return self.name == other.name and self.path == other.path


_BLOCK_RE = re.compile(r"\{%-?\s*block\s+(\w+)\s*-?%\}")


def _discover_layouts() -> dict[str, LayoutRecord]:
    """Scan the layouts package and register every .j2 file found."""
    registry: dict[str, LayoutRecord] = {}
    try:
        layouts_pkg = importlib.resources.files("aio.layouts")
        for resource in layouts_pkg.iterdir():
            name = resource.name
            if not name.endswith(".j2"):
                continue
            stem = name[:-3]
            try:
                content = resource.read_text(encoding="utf-8")
            except Exception as exc:
                _log.warning("Could not read layout '%s': %s", name, exc)
                continue
            raw_blocks = _BLOCK_RE.findall(content)
            # Deduplicate while preserving first-occurrence order
            seen: set[str] = set()
            unique_blocks: list[str] = []
            for block in raw_blocks:
                if block not in seen:
                    seen.add(block)
                    unique_blocks.append(block)
                else:
                    _log.warning("Duplicate block '%s' in layout '%s'", block, name)
            registry[stem] = LayoutRecord(name=stem, path=name, blocks=unique_blocks)
    except Exception as exc:
        _log.error("Layout discovery failed: %s", exc)
    return registry


LAYOUT_REGISTRY: dict[str, LayoutRecord] = _discover_layouts()
