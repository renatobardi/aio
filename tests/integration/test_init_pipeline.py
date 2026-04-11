"""End-to-end integration tests for `aio init` (US1)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import yaml


class TestInitPipelineE2E:
    """Full pipeline: subprocess `aio init`, assert files and timing."""

    def _run_init(  # noqa: E501
        self, tmp_path: Path, name: str, agent: str = "claude", theme: str = "minimal", extra: list[str] | None = None
    ) -> subprocess.CompletedProcess:
        cmd = [sys.executable, "-m", "aio", "init", name, "--agent", agent, "--theme", theme]
        if extra:
            cmd.extend(extra)
        return subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)

    def test_all_paths_exist(self, tmp_path: Path) -> None:
        result = self._run_init(tmp_path, "test-project")
        assert result.returncode == 0, f"stderr: {result.stderr}"

        project = tmp_path / "test-project"
        assert (project / ".aio").is_dir()
        assert (project / ".aio" / "config.yaml").is_file()
        assert (project / ".aio" / "meta.json").is_file()
        assert (project / ".aio" / "themes" / "registry.json").is_file()
        assert (project / "slides.md").is_file()
        assert (project / "assets").is_dir()
        assert (project / "build").is_dir()

    def test_config_yaml_parseable(self, tmp_path: Path) -> None:
        self._run_init(tmp_path, "test-project")
        config_path = tmp_path / "test-project" / ".aio" / "config.yaml"
        cfg = yaml.safe_load(config_path.read_text())
        assert isinstance(cfg, dict)
        assert cfg.get("agent") == "claude"
        assert cfg.get("theme") == "minimal"

    def test_meta_json_has_iso_created_at(self, tmp_path: Path) -> None:
        self._run_init(tmp_path, "test-project")
        meta_path = tmp_path / "test-project" / ".aio" / "meta.json"
        meta = json.loads(meta_path.read_text())
        assert "created_at" in meta
        # ISO 8601 format: e.g. "2024-01-15T12:00:00" or with timezone
        created_at = meta["created_at"]
        assert "T" in created_at or "-" in created_at  # basic ISO check

    def test_per_project_registry_single_theme_under_5kb(self, tmp_path: Path) -> None:
        self._run_init(tmp_path, "test-project")
        registry_path = tmp_path / "test-project" / ".aio" / "themes" / "registry.json"
        entries = json.loads(registry_path.read_text())
        assert len(entries) == 1, f"Expected 1 theme, got {len(entries)}"
        assert entries[0]["id"] == "minimal"
        assert registry_path.stat().st_size < 5 * 1024  # < 5 KB (SC-103)

    def test_init_completes_under_1_second(self, tmp_path: Path) -> None:
        start = time.perf_counter()
        result = self._run_init(tmp_path, "timing-project")
        elapsed = time.perf_counter() - start
        assert result.returncode == 0
        assert elapsed < 1.0, f"Init took {elapsed:.2f}s — must be < 1s (SC-100)"

    def test_invalid_agent_exits_nonzero(self, tmp_path: Path) -> None:
        result = self._run_init(tmp_path, "proj", agent="invalid-ai")
        assert result.returncode != 0

    def test_slides_md_has_frontmatter(self, tmp_path: Path) -> None:
        self._run_init(tmp_path, "test-project")
        slides = (tmp_path / "test-project" / "slides.md").read_text()
        assert slides.startswith("---")
        # Check YAML frontmatter fields
        front_end = slides.find("---", 3)
        frontmatter = yaml.safe_load(slides[3:front_end])
        assert "title" in frontmatter
        assert "agent" in frontmatter
        assert frontmatter["agent"] == "claude"

    def test_stdout_contains_success_message(self, tmp_path: Path) -> None:
        result = self._run_init(tmp_path, "my-deck")
        assert result.returncode == 0
        # Success message should mention project name or path
        output = result.stdout + result.stderr
        assert "my-deck" in output or "initialized" in output.lower()
