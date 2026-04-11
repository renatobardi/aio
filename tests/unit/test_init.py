"""Tests for `aio init` command (US1)."""

from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

runner = CliRunner()


def _get_app():
    from aio.cli import app

    return app


class TestInitCreatesStructure:
    """aio init creates all expected dirs and files."""

    def test_creates_all_8_paths(self, tmp_path: Path) -> None:
        app = _get_app()
        result = runner.invoke(
            app, ["init", "myproject", "--agent", "claude", "--theme", "minimal"], catch_exceptions=False
        )  # noqa: E501
        project_dir = tmp_path / "myproject"
        # Invoke in tmp_path context
        import os

        cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(
                app, ["init", "myproject", "--agent", "claude", "--theme", "minimal"], catch_exceptions=False
            )  # noqa: E501
        finally:
            os.chdir(cwd)

        assert result.exit_code == 0, result.output
        project_dir = tmp_path / "myproject"
        assert (project_dir / ".aio").is_dir()
        assert (project_dir / ".aio" / "config.yaml").is_file()
        assert (project_dir / ".aio" / "meta.json").is_file()
        assert (project_dir / ".aio" / "themes" / "registry.json").is_file()
        assert (project_dir / "slides.md").is_file()
        assert (project_dir / "assets").is_dir()
        assert (project_dir / "build").is_dir()

    def test_config_yaml_is_valid(self, tmp_path: Path) -> None:
        import os

        cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            app = _get_app()
            result = runner.invoke(
                app, ["init", "myproj", "--agent", "gemini", "--theme", "minimal"], catch_exceptions=False
            )  # noqa: E501
        finally:
            os.chdir(cwd)

        assert result.exit_code == 0
        config_path = tmp_path / "myproj" / ".aio" / "config.yaml"
        cfg = yaml.safe_load(config_path.read_text())
        assert cfg["agent"] == "gemini"
        assert cfg["theme"] == "minimal"

    def test_invalid_agent_exits_1_no_files(self, tmp_path: Path) -> None:
        import os

        cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            app = _get_app()
            result = runner.invoke(app, ["init", "proj", "--agent", "invalid-ai"])
        finally:
            os.chdir(cwd)

        assert result.exit_code == 1
        # No project directory should have been created
        assert not (tmp_path / "proj").exists()

    def test_invalid_agent_error_message(self, tmp_path: Path) -> None:
        import os

        cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            app = _get_app()
            result = runner.invoke(app, ["init", "proj", "--agent", "bad-agent"])
        finally:
            os.chdir(cwd)

        assert result.exit_code == 1
        combined = (result.output or "") + (result.stderr or "")
        assert "bad-agent" in combined.lower(), f"Expected 'bad-agent' in output: {combined!r}"

    def test_existing_aio_dir_exits_1_without_force(self, tmp_path: Path) -> None:
        import os

        cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            app = _get_app()
            # Create once
            runner.invoke(app, ["init", "proj", "--agent", "claude", "--theme", "minimal"])
            # Try again without --force
            result = runner.invoke(app, ["init", "proj", "--agent", "claude", "--theme", "minimal"])
        finally:
            os.chdir(cwd)

        assert result.exit_code == 1

    def test_force_flag_overwrites(self, tmp_path: Path) -> None:
        import os

        cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            app = _get_app()
            runner.invoke(app, ["init", "proj", "--agent", "claude", "--theme", "minimal"])
            result = runner.invoke(app, ["init", "proj", "--agent", "gemini", "--theme", "minimal", "--force"])
        finally:
            os.chdir(cwd)

        assert result.exit_code == 0
        cfg = yaml.safe_load((tmp_path / "proj" / ".aio" / "config.yaml").read_text())
        assert cfg["agent"] == "gemini"

    def test_dry_run_creates_no_files(self, tmp_path: Path) -> None:
        import os

        cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            app = _get_app()
            result = runner.invoke(app, ["init", "dryproj", "--agent", "claude", "--theme", "minimal", "--dry-run"])
        finally:
            os.chdir(cwd)

        assert result.exit_code == 0
        assert not (tmp_path / "dryproj").exists()


class TestInitRegistrySubset:
    """.aio/themes/registry.json must contain only the selected theme."""

    def test_per_project_registry_is_minimal(self, tmp_path: Path) -> None:
        import json
        import os

        cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            app = _get_app()
            runner.invoke(app, ["init", "proj", "--agent", "claude", "--theme", "minimal"], catch_exceptions=False)
        finally:
            os.chdir(cwd)

        registry_path = tmp_path / "proj" / ".aio" / "themes" / "registry.json"
        assert registry_path.stat().st_size < 5 * 1024  # < 5 KB (SC-103)
        entries = json.loads(registry_path.read_text())
        assert len(entries) == 1
        assert entries[0]["id"] == "minimal"
