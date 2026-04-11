"""Tests for ProjectConfig (US1 + US5)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from tests.conftest import write_config

# ---------------------------------------------------------------------------
# US1: ProjectConfig basic behaviour
# ---------------------------------------------------------------------------


class TestProjectConfigLoad:
    """ProjectConfig.load() reads all fields from YAML."""

    def test_loads_all_fields(self, tmp_path: Path) -> None:
        write_config(
            tmp_path,
            {
                "agent": "claude",
                "theme": "minimal",
                "enrich": True,
                "serve_port": 9000,
                "output_dir": "out",
            },
        )
        from aio.commands.init import ProjectConfig

        cfg = ProjectConfig.load(tmp_path / ".aio")
        assert cfg.agent == "claude"
        assert cfg.theme == "minimal"
        assert cfg.enrich is True
        assert cfg.serve_port == 9000
        assert cfg.output_dir == "out"

    def test_defaults_applied_when_minimal(self, tmp_path: Path) -> None:
        write_config(tmp_path, {"agent": "claude"})
        from aio.commands.init import ProjectConfig

        cfg = ProjectConfig.load(tmp_path / ".aio")
        assert cfg.theme == "minimal"  # "default" alias resolved
        assert cfg.enrich is False
        assert cfg.serve_port == 8000
        assert cfg.output_dir == "build"

    def test_default_theme_alias_resolved(self, tmp_path: Path) -> None:
        write_config(tmp_path, {"agent": "gemini", "theme": "default"})
        from aio.commands.init import ProjectConfig

        cfg = ProjectConfig.load(tmp_path / ".aio")
        assert cfg.theme == "minimal"

    def test_invalid_agent_raises_config_error(self, tmp_path: Path) -> None:
        write_config(tmp_path, {"agent": "invalid-ai"})
        from aio.commands.init import ProjectConfig
        from aio.exceptions import ConfigError

        with pytest.raises(ConfigError) as exc_info:
            ProjectConfig.load(tmp_path / ".aio")
        assert "invalid-ai" in str(exc_info.value)

    def test_all_8_agents_accepted(self, tmp_path: Path) -> None:
        agents = ["claude", "gemini", "copilot", "windsurf", "devin", "chatgpt", "cursor", "generic"]
        from aio.commands.init import ProjectConfig

        for agent in agents:
            write_config(tmp_path, {"agent": agent})
            cfg = ProjectConfig.load(tmp_path / ".aio")
            assert cfg.agent == agent

    def test_load_timing(self, tmp_path: Path) -> None:
        write_config(tmp_path, {"agent": "claude"})
        from aio.commands.init import ProjectConfig

        start = time.perf_counter()
        ProjectConfig.load(tmp_path / ".aio")
        elapsed = time.perf_counter() - start
        assert elapsed < 0.010, f"Config load took {elapsed:.4f}s — must be < 10ms (SC-106)"


class TestProjectConfigImmutability:
    """ProjectConfig is frozen (immutable after construction)."""

    def test_frozen_raises_on_mutation(self, tmp_path: Path) -> None:
        write_config(tmp_path, {"agent": "claude"})
        from aio.commands.init import ProjectConfig

        cfg = ProjectConfig.load(tmp_path / ".aio")
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            cfg.agent = "gemini"  # type: ignore[misc]


class TestProjectConfigToDict:
    """ProjectConfig.to_dict() serializes all fields."""

    def test_to_dict_returns_all_fields(self, tmp_path: Path) -> None:
        write_config(tmp_path, {"agent": "gemini", "theme": "modern"})
        from aio.commands.init import ProjectConfig

        cfg = ProjectConfig.load(tmp_path / ".aio")
        d = cfg.to_dict()
        assert d["agent"] == "gemini"
        assert d["theme"] == "modern"
        assert "enrich" in d
        assert "serve_port" in d
        assert "output_dir" in d

    def test_to_dict_reflects_alias(self, tmp_path: Path) -> None:
        write_config(tmp_path, {"agent": "claude", "theme": "default"})
        from aio.commands.init import ProjectConfig

        cfg = ProjectConfig.load(tmp_path / ".aio")
        d = cfg.to_dict()
        assert d["theme"] == "minimal"


# ---------------------------------------------------------------------------
# US5: Config auto-load and CLI override
# ---------------------------------------------------------------------------


class TestConfigAutoLoad:
    """Config is loaded from nearest .aio/ ancestor."""

    def test_missing_aio_dir_raises(self, tmp_path: Path) -> None:
        from aio._utils import find_aio_dir
        from aio.exceptions import AIOError

        # tmp_path has no .aio/ dir
        with pytest.raises(AIOError):
            find_aio_dir(tmp_path)

    def test_finds_aio_dir_in_parent(self, tmp_path: Path) -> None:
        aio_dir = tmp_path / ".aio"
        aio_dir.mkdir()
        subdir = tmp_path / "sub" / "dir"
        subdir.mkdir(parents=True)

        from aio._utils import find_aio_dir

        found = find_aio_dir(subdir)
        assert found == aio_dir

    def test_project_config_load_timing(self, tmp_path: Path) -> None:
        write_config(tmp_path, {"agent": "claude"})
        from aio.commands.init import ProjectConfig

        start = time.perf_counter()
        ProjectConfig.load(tmp_path / ".aio")
        elapsed = time.perf_counter() - start
        assert elapsed < 0.010, f"Config load took {elapsed:.4f}s — must be < 10ms"
