"""DESIGN.md schema validation for AIO themes (Art. V — 11 sections mandatory)."""
from __future__ import annotations

import importlib.resources

from aio._log import get_logger
from aio.exceptions import ThemeNotFoundError

_log = get_logger(__name__)

REQUIRED_SECTIONS = [
    "Visual Theme",
    "Color Palette",
    "Typography",
    "Components",
    "Layout System",
    "Depth & Shadows",
    "Do's & Don'ts",
    "Responsive Behavior",
    "Animation & Transitions",
    "Accessibility",
    "Agent Prompt Snippet",
]


def validate_theme(theme_id: str) -> list[str]:
    """
    Validate a theme's DESIGN.md for schema compliance.

    Returns a list of error strings (empty if valid).
    Raises ThemeNotFoundError if theme_id is not in the global registry.
    """
    from aio.themes.loader import load_registry

    registry = load_registry()
    theme_entry = next((t for t in registry if t["id"] == theme_id), None)
    if theme_entry is None:
        raise ThemeNotFoundError(theme_id)

    try:
        design_ref = importlib.resources.files("aio.themes") / theme_id / "DESIGN.md"
        design_text = design_ref.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"Cannot read DESIGN.md for theme '{theme_id}': {exc}"]

    errors: list[str] = []
    for section in REQUIRED_SECTIONS:
        if section not in design_text:
            errors.append(f"Missing section: '{section}'")

    if errors:
        _log.warning("Theme '%s' has %d validation error(s)", theme_id, len(errors))
    else:
        _log.debug("Theme '%s' passed all validation checks", theme_id)

    return errors
