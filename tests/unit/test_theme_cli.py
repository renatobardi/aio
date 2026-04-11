"""Unit tests for the aio theme CLI subcommands (T036)."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from aio.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# aio theme list
# ---------------------------------------------------------------------------

def test_theme_list_exits_0() -> None:
    result = runner.invoke(app, ["theme", "list"])
    assert result.exit_code == 0, result.output


def test_theme_list_shows_id_and_name_columns() -> None:
    result = runner.invoke(app, ["theme", "list"])
    assert result.exit_code == 0
    assert "ID" in result.output or "minimal" in result.output


def test_theme_list_json_is_valid_array() -> None:
    result = runner.invoke(app, ["theme", "list", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 1


def test_theme_list_json_entries_have_required_keys() -> None:
    result = runner.invoke(app, ["theme", "list", "--json"])
    data = json.loads(result.output)
    for entry in data:
        assert "id" in entry
        assert "name" in entry


def test_theme_list_filter_reduces_results() -> None:
    result_all = runner.invoke(app, ["theme", "list", "--json"])
    result_filtered = runner.invoke(app, ["theme", "list", "--json", "--filter", "nonexistent-tag-xyz"])
    all_data = json.loads(result_all.output)
    filtered_data = json.loads(result_filtered.output)
    assert len(filtered_data) < len(all_data) or len(filtered_data) == 0


def test_theme_list_filter_matches_category() -> None:
    result = runner.invoke(app, ["theme", "list", "--json", "--filter", "minimal"])
    data = json.loads(result.output)
    assert any(e["id"] == "minimal" for e in data)


def test_theme_list_limit_restricts_count() -> None:
    result = runner.invoke(app, ["theme", "list", "--json", "--limit", "1"])
    data = json.loads(result.output)
    assert len(data) <= 1


def test_theme_list_search_finds_minimal() -> None:
    result = runner.invoke(app, ["theme", "list", "--json", "--search", "minimal"])
    data = json.loads(result.output)
    ids = [e["id"] for e in data]
    assert "minimal" in ids


# ---------------------------------------------------------------------------
# aio theme search
# ---------------------------------------------------------------------------

def test_theme_search_exits_0() -> None:
    result = runner.invoke(app, ["theme", "search", "minimal"])
    assert result.exit_code == 0, result.output


def test_theme_search_returns_results() -> None:
    result = runner.invoke(app, ["theme", "search", "minimal", "--json"])
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 1


def test_theme_search_json_has_score_field() -> None:
    result = runner.invoke(app, ["theme", "search", "minimal", "--json"])
    data = json.loads(result.output)
    for entry in data:
        assert "score" in entry
        assert 0.0 <= float(entry["score"]) <= 1.0


def test_theme_search_sorted_by_score_desc() -> None:
    result = runner.invoke(app, ["theme", "search", "min", "--json"])
    data = json.loads(result.output)
    if len(data) >= 2:
        scores = [float(e["score"]) for e in data]
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# aio theme info
# ---------------------------------------------------------------------------

def test_theme_info_known_theme_exits_0() -> None:
    result = runner.invoke(app, ["theme", "info", "minimal"])
    assert result.exit_code == 0, result.output


def test_theme_info_shows_name_and_colors() -> None:
    result = runner.invoke(app, ["theme", "info", "minimal"])
    assert "minimal" in result.output.lower() or "Minimal" in result.output


def test_theme_info_json_output() -> None:
    result = runner.invoke(app, ["theme", "info", "minimal", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "minimal"
    assert "colors" in data
    assert "typography" in data


def test_theme_info_unknown_exits_2() -> None:
    result = runner.invoke(app, ["theme", "info", "nonexistent-theme-xyz"])
    assert result.exit_code == 2


# ---------------------------------------------------------------------------
# aio theme show
# ---------------------------------------------------------------------------

def test_theme_show_exits_0() -> None:
    result = runner.invoke(app, ["theme", "show", "minimal"])
    assert result.exit_code == 0, result.output


def test_theme_show_section_filter() -> None:
    result = runner.invoke(app, ["theme", "show", "minimal", "--section", "2"])
    assert result.exit_code == 0
    # Section 2 = Color Palette
    assert "Color Palette" in result.output or "#" in result.output


def test_theme_show_unknown_theme_exits_2() -> None:
    result = runner.invoke(app, ["theme", "show", "nonexistent-xyz"])
    assert result.exit_code == 2


def test_theme_show_section_out_of_range_exits_3() -> None:
    result = runner.invoke(app, ["theme", "show", "minimal", "--section", "99"])
    assert result.exit_code == 3


# ---------------------------------------------------------------------------
# aio theme use
# ---------------------------------------------------------------------------

def test_theme_use_no_project_dir_exits_3(tmp_path) -> None:
    result = runner.invoke(app, ["theme", "use", "minimal", "--project-dir", str(tmp_path)])
    assert result.exit_code == 3, f"Expected exit 3 (no .aio dir), got {result.exit_code}"


def test_theme_use_unknown_theme_exits_2(tmp_path) -> None:
    result = runner.invoke(app, ["theme", "use", "nonexistent-xyz", "--project-dir", str(tmp_path)])
    assert result.exit_code == 2


def test_theme_use_updates_config(tmp_path) -> None:
    import yaml

    aio_dir = tmp_path / ".aio"
    aio_dir.mkdir()
    config = {"theme": "modern", "agent": "default"}
    (aio_dir / "config.yaml").write_text(yaml.dump(config))
    (aio_dir / "themes").mkdir()

    result = runner.invoke(app, ["theme", "use", "minimal", "--project-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output

    updated = yaml.safe_load((aio_dir / "config.yaml").read_text())
    assert updated["theme"] == "minimal"


# ---------------------------------------------------------------------------
# aio theme create
# ---------------------------------------------------------------------------

def test_theme_create_invalid_name_exits_4() -> None:
    result = runner.invoke(app, ["theme", "create", "My Theme!!", "--project-dir", "/tmp"])
    assert result.exit_code == 4


def test_theme_create_valid_name_in_project(tmp_path) -> None:
    aio_dir = tmp_path / ".aio"
    aio_dir.mkdir()
    (aio_dir / "themes").mkdir()

    result = runner.invoke(app, ["theme", "create", "my-custom", "--project-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert (aio_dir / "themes" / "my-custom").exists()


def test_theme_create_from_existing(tmp_path) -> None:
    aio_dir = tmp_path / ".aio"
    aio_dir.mkdir()
    (aio_dir / "themes").mkdir()

    result = runner.invoke(
        app, ["theme", "create", "my-stripe", "--from", "minimal", "--project-dir", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    theme_dir = aio_dir / "themes" / "my-stripe"
    assert theme_dir.exists()
    assert (theme_dir / "theme.css").exists()
