"""DESIGN.md schema validation for AIO themes (Art. V — 11 sections mandatory)."""

from __future__ import annotations

import importlib.resources

from aio._log import get_logger
from aio.exceptions import DesignSectionParseError, DesignSectionValidationError, ThemeNotFoundError
from aio.themes.parser import parse_design_md

_log = get_logger(__name__)


def validate_theme(theme_id: str) -> list[str]:
    """
    Validate a theme's DESIGN.md for schema compliance.

    Returns a list of error strings (empty if valid).
    Raises ThemeNotFoundError if theme_id is not in the global registry.
    """
    from aio.themes.loader import load_registry

    registry = load_registry()
    theme_entry = next((t for t in registry if (t["id"] if isinstance(t, dict) else t.id) == theme_id), None)
    if theme_entry is None:
        raise ThemeNotFoundError(theme_id)

    try:
        design_ref = importlib.resources.files("aio.themes") / theme_id / "DESIGN.md"
        design_text = design_ref.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"Cannot read DESIGN.md for theme '{theme_id}': {exc}"]

    errors: list[str] = []

    try:
        sections = parse_design_md(design_text)
    except DesignSectionParseError as exc:
        errors.append(str(exc))
        _log.warning("Theme '%s' failed structural parse: %s", theme_id, exc)
        return errors
    except DesignSectionValidationError as exc:
        errors.append(str(exc))
        _log.warning("Theme '%s' failed content validation: %s", theme_id, exc)
        return errors

    # Validate that each section has meaningful content
    for s in sections:
        if s.char_count == 0:
            errors.append(f"Section {s.section_number} ('{s.heading}') is empty.")

    if errors:
        _log.warning("Theme '%s' has %d validation error(s)", theme_id, len(errors))
    else:
        _log.debug("Theme '%s' passed all validation checks (%d sections)", theme_id, len(sections))

    return errors
