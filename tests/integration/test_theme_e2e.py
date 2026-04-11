"""Integration tests for theme loading — registry, ThemeRecord paths, validation (T035)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aio.themes.loader import ThemeRecord, load_registry
from aio.themes.validator import validate_theme

FIXTURE_THEME_DIR = Path(__file__).parent.parent / "fixtures" / "themes" / "fixture_theme"


# ---------------------------------------------------------------------------
# load_registry
# ---------------------------------------------------------------------------


def test_load_registry_returns_list() -> None:
    registry = load_registry()
    assert isinstance(registry, list), "load_registry() must return a list"


def test_load_registry_has_at_least_one_builtin() -> None:
    registry = load_registry()
    assert len(registry) >= 1, "Registry must contain at least the built-in themes"


def test_load_registry_all_entries_are_theme_records() -> None:
    registry = load_registry()
    for record in registry:
        assert isinstance(record, ThemeRecord)


def test_load_registry_css_paths_exist() -> None:
    registry = load_registry()
    for record in registry:
        assert record.css_path.exists(), f"theme.css missing for '{record.id}': {record.css_path}"


def test_load_registry_layout_css_paths_exist() -> None:
    registry = load_registry()
    for record in registry:
        assert record.layout_css_path.exists(), f"layout.css missing for '{record.id}': {record.layout_css_path}"


def test_load_registry_colors_have_primary() -> None:
    registry = load_registry()
    for record in registry:
        assert "primary" in record.colors, f"Theme '{record.id}' missing 'primary' color"


def test_load_registry_typography_has_heading_font() -> None:
    registry = load_registry()
    for record in registry:
        assert "heading_font" in record.typography, f"Theme '{record.id}' missing 'heading_font' typography"


# ---------------------------------------------------------------------------
# ThemeRecord path resolution for fixture_theme
# ---------------------------------------------------------------------------


def test_fixture_theme_record_from_dict() -> None:
    meta = {
        "id": "fixture_theme",
        "name": "Fixture Theme",
        "description": "Test theme",
        "version": "1.0.0",
        "author": "AIO",
        "source_url": None,
        "categories": ["test"],
        "colors": {"primary": "#1a56db", "background": "#ffffff", "text": "#111827"},
        "typography": {"heading_font": "Inter", "body_font": "Inter"},
        "is_builtin": False,
    }
    record = ThemeRecord.from_dict(meta, base_dir=FIXTURE_THEME_DIR)
    assert record.css_path == FIXTURE_THEME_DIR / "theme.css"
    assert record.layout_css_path == FIXTURE_THEME_DIR / "layout.css"
    assert record.design_md_path == FIXTURE_THEME_DIR / "DESIGN.md"


def test_fixture_theme_css_path_exists() -> None:
    meta = {
        "id": "fixture_theme",
        "name": "Fixture Theme",
        "colors": {"primary": "#1a56db", "background": "#ffffff", "text": "#111827"},
        "typography": {"heading_font": "Inter", "body_font": "Inter"},
        "categories": [],
        "author": "",
        "source_url": None,
    }
    record = ThemeRecord.from_dict(meta, base_dir=FIXTURE_THEME_DIR)
    assert record.css_path.exists(), f"theme.css not found at {record.css_path}"
    assert record.layout_css_path.exists(), f"layout.css not found at {record.layout_css_path}"
    assert record.design_md_path is not None and record.design_md_path.exists(), (
        f"DESIGN.md not found at {FIXTURE_THEME_DIR / 'DESIGN.md'}"
    )


# ---------------------------------------------------------------------------
# validate_theme — uses the installed package themes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("theme_id", ["minimal", "modern", "vibrant"])
def test_builtin_theme_validates_without_errors(theme_id: str) -> None:
    errors = validate_theme(theme_id)
    assert errors == [], f"Theme '{theme_id}' has validation errors: {errors}"
