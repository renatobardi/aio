"""Shared pytest fixtures for AIO tests."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Path:
    """Temporary directory with a minimal .aio/ scaffold."""
    aio_dir = tmp_path / ".aio"
    aio_dir.mkdir()
    (aio_dir / "themes").mkdir()
    return tmp_path


@pytest.fixture
def minimal_config_yaml() -> bytes:
    """Minimal valid config.yaml content."""
    return b"agent: claude\n"


@pytest.fixture
def sample_slides_md() -> str:
    """3-slide markdown string for parser tests."""
    return """\
---
title: Test Deck
agent: claude
theme: minimal
---

# Slide 1

<!-- @layout: hero-title -->
<!-- @title: Welcome -->

Content here.

---

# Slide 2

<!-- @layout: content -->

More content.

---

# Slide 3

Final slide.
"""


def write_config(path: Path, data: dict) -> None:
    """Helper: write a config.yaml inside {path}/.aio/."""
    aio_dir = path / ".aio"
    aio_dir.mkdir(parents=True, exist_ok=True)
    (aio_dir / "config.yaml").write_text(
        yaml.dump(data, default_flow_style=False), encoding="utf-8"
    )
