"""Unit tests for ThemeRecord loading and load_registry() (T030)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aio.exceptions import ThemeValidationError
from aio.themes.loader import ThemeRecord, load_registry

FIXTURE_THEME_DIR = Path(__file__).parent.parent / "fixtures" / "themes" / "fixture_theme"


# ---------------------------------------------------------------------------
# ThemeRecord.from_dict — happy path
# ---------------------------------------------------------------------------


def test_from_dict_valid_meta() -> None:
    meta = {
        "id": "fixture_theme",
        "name": "Fixture Theme",
        "colors": {"primary": "#1a56db", "accent": "#e74694", "background": "#ffffff", "text": "#111827"},
        "typography": {"heading_font": "Inter", "body_font": "Inter"},
        "categories": ["test"],
        "author": "AIO",
        "source_url": "",
    }
    record = ThemeRecord.from_dict(meta, base_dir=FIXTURE_THEME_DIR)
    assert record.id == "fixture_theme"
    assert record.name == "Fixture Theme"
    assert record.colors["primary"] == "#1a56db"
    assert record.typography["heading_font"] == "Inter"
    assert record.base_dir == FIXTURE_THEME_DIR


def test_from_dict_css_path_resolved() -> None:
    meta = {
        "id": "fixture_theme",
        "name": "Fixture Theme",
        "colors": {"primary": "#1a56db", "background": "#ffffff", "text": "#111827"},
        "typography": {"heading_font": "Inter", "body_font": "Inter"},
        "categories": [],
        "author": "",
        "source_url": "",
    }
    record = ThemeRecord.from_dict(meta, base_dir=FIXTURE_THEME_DIR)
    assert record.css_path == FIXTURE_THEME_DIR / "theme.css"
    assert record.layout_css_path == FIXTURE_THEME_DIR / "layout.css"
    assert record.design_md_path == FIXTURE_THEME_DIR / "DESIGN.md"


def test_from_dict_defaults_for_optional_fields(tmp_path: Path) -> None:
    meta = {
        "id": "x",
        "name": "X",
        "colors": {"primary": "#000", "background": "#fff", "text": "#000"},
        "typography": {"heading_font": "Sans", "body_font": "Sans"},
        "categories": [],
        "author": "",
        "source_url": "",
    }
    record = ThemeRecord.from_dict(meta, base_dir=tmp_path)
    assert record.categories == []
    assert record.author == ""
    assert record.source_url is None


# ---------------------------------------------------------------------------
# ThemeRecord.from_dict — validation errors
# ---------------------------------------------------------------------------


def test_from_dict_missing_id_raises(tmp_path: Path) -> None:
    meta = {
        "name": "No ID",
        "colors": {"primary": "#000"},
        "typography": {},
        "categories": [],
        "author": "",
        "source_url": "",
    }
    with pytest.raises(ThemeValidationError):
        ThemeRecord.from_dict(meta, base_dir=tmp_path)


def test_from_dict_missing_name_raises(tmp_path: Path) -> None:
    meta = {
        "id": "x",
        "colors": {"primary": "#000"},
        "typography": {},
        "categories": [],
        "author": "",
        "source_url": "",
    }
    with pytest.raises(ThemeValidationError):
        ThemeRecord.from_dict(meta, base_dir=tmp_path)


def test_from_dict_missing_primary_color_raises(tmp_path: Path) -> None:
    meta = {
        "id": "x",
        "name": "X",
        "colors": {"accent": "#fff"},  # no "primary"
        "typography": {},
        "categories": [],
        "author": "",
        "source_url": "",
    }
    with pytest.raises(ThemeValidationError):
        ThemeRecord.from_dict(meta, base_dir=tmp_path)


# ---------------------------------------------------------------------------
# load_registry
# ---------------------------------------------------------------------------


def test_load_registry_returns_list() -> None:
    registry = load_registry()
    assert isinstance(registry, list)


def test_load_registry_at_least_one_entry() -> None:
    registry = load_registry()
    assert len(registry) >= 1, "Registry must have at least 1 theme (minimal entry)"


def test_load_registry_entries_are_theme_records() -> None:
    registry = load_registry()
    for entry in registry:
        assert isinstance(entry, ThemeRecord), f"Expected ThemeRecord, got {type(entry)}"
        assert entry.id, "ThemeRecord.id must not be empty"
        assert entry.name, "ThemeRecord.name must not be empty"
