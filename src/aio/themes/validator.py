"""DESIGN.md schema validation for AIO themes (Art. V — 11 sections mandatory)."""

from __future__ import annotations

import importlib.resources
import re

from aio._log import get_logger
from aio.exceptions import DesignSectionParseError, DesignSectionValidationError, ThemeNotFoundError
from aio.themes.parser import parse_design_md

_log = get_logger(__name__)

# ---------------------------------------------------------------------------
# CSS validation helpers (additive, non-breaking)
# ---------------------------------------------------------------------------


def validate_css_string(css_text: str) -> list[str]:
    """Parse CSS with cssutils and return a list of error/warning messages.

    Returns an empty list if cssutils is not installed or if the CSS is valid.
    This is additive — callers that don't opt in (check_css=False) never call this.
    """
    if not css_text.strip():
        return []
    try:
        import logging as _logging

        import cssutils

        # Suppress cssutils internal log spam
        cssutils.log.setLevel(_logging.CRITICAL)
        sheet = cssutils.parseString(css_text, validate=True)
        errors: list[str] = []
        for rule in sheet:
            if hasattr(rule, "style"):
                for prop in rule.style:
                    # CSS custom properties (--*) are always valid; cssutils predates them
                    if not prop.valid and not prop.name.startswith("--"):
                        errors.append(f"Invalid CSS property: {prop.name}: {prop.value}")
        return errors
    except ImportError:
        _log.debug("cssutils not available; CSS validation skipped")
        return []
    except Exception as exc:  # noqa: BLE001
        _log.debug("cssutils parse error: %s", exc)
        return [f"CSS parse error: {exc}"]


def wcag_contrast_ratio(hex1: str, hex2: str) -> float:
    """Compute WCAG 2.1 contrast ratio between two hex colors.

    Args:
        hex1: First color as #RRGGBB or #RGB string.
        hex2: Second color as #RRGGBB or #RGB string.

    Returns:
        Contrast ratio (1.0–21.0).

    Raises:
        ValueError: If either hex string is malformed.
    """

    def _relative_luminance(hex_color: str) -> float:
        h = hex_color.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) != 6 or not all(c in "0123456789ABCDEFabcdef" for c in h):
            raise ValueError(f"Invalid hex color: {hex_color!r}")
        r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255

        def _linearize(c: float) -> float:
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)

    l1 = _relative_luminance(hex1)
    l2 = _relative_luminance(hex2)
    lighter, darker = (l1, l2) if l1 > l2 else (l2, l1)
    return (lighter + 0.05) / (darker + 0.05)


def validate_theme(theme_id: str, check_css: bool = False) -> list[str]:
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

    # Optional CSS validation (additive, non-breaking — defaults to False)
    if check_css:
        try:
            css_ref = importlib.resources.files("aio.themes") / theme_id / "theme.css"
            css_text = css_ref.read_text(encoding="utf-8")
            css_errors = validate_css_string(css_text)
            errors.extend(css_errors)

            # WCAG contrast check on --color-* CSS custom properties in :root
            _hex_re = re.compile(r"--(color-[^:]+)\s*:\s*(#[0-9A-Fa-f]{3,6})")
            color_vars: dict[str, str] = {}
            for m in _hex_re.finditer(css_text):
                color_vars[m.group(1)] = m.group(2)

            bg_hex = color_vars.get("color-background") or color_vars.get("color-bg")
            primary_hex = color_vars.get("color-primary")
            if bg_hex and primary_hex:
                try:
                    ratio = wcag_contrast_ratio(primary_hex, bg_hex)
                    if ratio < 4.5:
                        errors.append(
                            f"WCAG AA contrast fail: --color-primary ({primary_hex}) on "
                            f"--color-background ({bg_hex}) = {ratio:.2f}:1 (need ≥ 4.5:1)"
                        )
                except ValueError as exc:
                    _log.debug("Contrast check skipped: %s", exc)
        except Exception as exc:  # noqa: BLE001
            _log.debug("CSS validation skipped for theme '%s': %s", theme_id, exc)

    return errors
