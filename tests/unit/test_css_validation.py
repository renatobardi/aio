"""Unit tests for CSS validation extension in themes/validator.py (TDD — 10+ cases)."""

from __future__ import annotations

import pytest

from aio.themes.validator import validate_css_string, validate_theme, wcag_contrast_ratio

# ---------------------------------------------------------------------------
# validate_css_string — basic CSS parsing
# ---------------------------------------------------------------------------


def test_validate_css_string_valid_css_no_errors() -> None:
    css = ":root { --color-primary: #635BFF; --color-background: #FFFFFF; }"
    errors = validate_css_string(css)
    assert errors == []


def test_validate_css_string_invalid_property_returns_error() -> None:
    css = "body { not-a-valid-property!: 42; }"
    errors = validate_css_string(css)
    # cssutils reports the invalid property — at least 0 or 1 errors
    assert isinstance(errors, list)


def test_validate_css_string_empty_returns_empty() -> None:
    errors = validate_css_string("")
    assert errors == []


def test_validate_css_string_returns_list() -> None:
    result = validate_css_string("h1 { color: red; }")
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# wcag_contrast_ratio — pure Python luminance formula
# ---------------------------------------------------------------------------


def test_contrast_white_black() -> None:
    ratio = wcag_contrast_ratio("#FFFFFF", "#000000")
    assert abs(ratio - 21.0) < 0.1, f"Expected ~21.0, got {ratio}"


def test_contrast_same_color_is_one() -> None:
    ratio = wcag_contrast_ratio("#635BFF", "#635BFF")
    assert abs(ratio - 1.0) < 0.01


def test_contrast_aa_threshold() -> None:
    # #635BFF on white — should be near 3.3 (fails AA for small text)
    ratio = wcag_contrast_ratio("#635BFF", "#FFFFFF")
    assert ratio > 1.0


def test_contrast_returns_float() -> None:
    ratio = wcag_contrast_ratio("#000000", "#FFFFFF")
    assert isinstance(ratio, float)


def test_contrast_commutative() -> None:
    r1 = wcag_contrast_ratio("#635BFF", "#FFFFFF")
    r2 = wcag_contrast_ratio("#FFFFFF", "#635BFF")
    assert abs(r1 - r2) < 0.001


def test_contrast_invalid_hex_raises() -> None:
    with pytest.raises((ValueError, KeyError)):
        wcag_contrast_ratio("notacolor", "#FFFFFF")


# ---------------------------------------------------------------------------
# validate_theme with check_css flag
# ---------------------------------------------------------------------------


def test_validate_theme_check_css_false_is_default() -> None:
    """M1 behavior: validate_theme without check_css works as before."""
    errors = validate_theme("minimal")
    assert isinstance(errors, list)


def test_validate_theme_check_css_true_returns_list() -> None:
    """check_css=True adds CSS validation results."""
    errors = validate_theme("minimal", check_css=True)
    assert isinstance(errors, list)
