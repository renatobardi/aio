"""Theme path resolution, ThemeRecord dataclass, and registry loading via importlib.resources."""

from __future__ import annotations

import importlib.resources
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aio._log import get_logger
from aio.exceptions import ThemeValidationError
from aio.themes.parser import DecorationSpec, create_default_visual_config, extract_visual_style_config, parse_design_md

_log = get_logger(__name__)

# Required color keys per data-model.md
_REQUIRED_COLOR_KEYS = {"primary", "background", "text"}
# Required typography keys per data-model.md
_REQUIRED_TYPOGRAPHY_KEYS = {"heading_font", "body_font"}
# Hex color pattern
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$")


@dataclass
class ThemeRecord:
    """One theme entry, fully resolved with file paths. Constructed via from_dict()."""

    id: str
    name: str
    description: str
    version: str
    author: str
    source_url: str | None
    categories: list[str]
    colors: dict[str, str]
    typography: dict[str, str]
    css_path: Path
    layout_css_path: Path
    design_md_path: Path | None
    is_builtin: bool
    base_dir: Path
    decorations: list[DecorationSpec] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, Any], base_dir: Path) -> ThemeRecord:
        """
        Deserialise a registry.json entry dict into a ThemeRecord.

        Raises ThemeValidationError if required fields are missing or invalid.
        """
        errors: list[str] = []

        theme_id = d.get("id", "").strip()
        if not theme_id:
            errors.append("'id' is required and must be non-empty.")

        name = d.get("name", "").strip()
        if not name:
            errors.append("'name' is required and must be non-empty.")

        colors = d.get("colors", {}) or {}
        missing_colors = _REQUIRED_COLOR_KEYS - set(colors.keys())
        if missing_colors:
            errors.append(f"'colors' is missing required keys: {sorted(missing_colors)}")

        typography = d.get("typography", {}) or {}
        missing_typo = _REQUIRED_TYPOGRAPHY_KEYS - set(typography.keys())
        if missing_typo:
            errors.append(f"'typography' is missing required keys: {sorted(missing_typo)}")

        if errors:
            raise ThemeValidationError(theme_id or "<unknown>", errors)

        # Resolve paths
        css_path = base_dir / "theme.css"
        layout_css_path = base_dir / "layout.css"
        design_md_path = base_dir / "DESIGN.md"

        # Parse DESIGN.md section 10 for visual_config, with defaults fallback
        metadata: dict[str, Any] = {}
        visual_config: dict[str, object] = {}

        if design_md_path.exists():
            try:
                design_text = design_md_path.read_text(encoding="utf-8")
                sections = parse_design_md(design_text)
                visual_config = extract_visual_style_config(sections)
                if visual_config:
                    _log.debug("Theme '%s': extracted visual_config from DESIGN.md section 10", theme_id)
                else:
                    _log.warning(
                        "Theme '%s': DESIGN.md section 10 (Visual Style Preference) not found or incomplete; "
                        "using defaults (tech/geometric/sharp/static)",
                        theme_id,
                    )
            except Exception as exc:
                _log.warning(
                    "Theme '%s': could not parse DESIGN.md section 10: %s; "
                    "using defaults (tech/geometric/sharp/static)",
                    theme_id,
                    exc,
                )

        # Always provide visual_config (defaults: tech/geometric/sharp/static)
        metadata["visual_config"] = {**create_default_visual_config(), **visual_config}

        return cls(
            id=theme_id,
            name=name,
            description=d.get("description", ""),
            version=d.get("version", "1.0.0"),
            author=d.get("author", "unknown"),
            source_url=d.get("source_url") or None,
            categories=list(d.get("categories", [])),
            colors=dict(colors),
            typography=dict(typography),
            css_path=css_path,
            layout_css_path=layout_css_path,
            design_md_path=design_md_path if design_md_path.exists() else None,
            is_builtin=bool(d.get("is_builtin", False)),
            base_dir=base_dir,
            metadata=metadata,
        )


def load_registry() -> list[ThemeRecord]:
    """
    Load the global theme registry from src/aio/themes/registry.json.

    Returns a list of ThemeRecord objects. Entries with missing CSS files are
    skipped with a warning (partial success). Returns empty list only if
    registry.json cannot be read.
    """
    try:
        themes_ref = importlib.resources.files("aio.themes")
        data = themes_ref.joinpath("registry.json").read_text(encoding="utf-8")
        raw_entries: list[dict[str, Any]] = json.loads(data)
    except Exception as exc:
        _log.error("Failed to load theme registry: %s", exc)
        return []

    # Resolve the base directory for the themes package
    try:
        themes_base = Path(str(themes_ref))
    except Exception:
        themes_base = Path(__file__).parent

    records: list[ThemeRecord] = []
    for entry in raw_entries:
        theme_id = str(entry.get("id", "<unknown>"))
        theme_dir = themes_base / theme_id
        try:
            record = ThemeRecord.from_dict(entry, base_dir=theme_dir)
        except ThemeValidationError as exc:
            _log.warning("Skipping theme '%s': validation error — %s", theme_id, exc)
            continue

        if not record.css_path.exists():
            _log.warning("Skipping theme '%s': theme.css not found at %s", theme_id, record.css_path)
            continue
        if not record.layout_css_path.exists():
            _log.warning("Skipping theme '%s': layout.css not found at %s", theme_id, record.layout_css_path)
            continue

        records.append(record)
        _log.debug("Loaded theme '%s' from %s", theme_id, theme_dir)

    _log.debug("Registry loaded: %d themes", len(records))
    return records


def resolve_theme_path(theme_id: str) -> Path:
    """
    Return the filesystem path to a theme directory.

    Uses importlib.resources — works in pip and development modes.
    For zipapp/PyInstaller, callers should use files() API directly.
    """
    ref = importlib.resources.files("aio.themes") / theme_id
    return Path(str(ref))
