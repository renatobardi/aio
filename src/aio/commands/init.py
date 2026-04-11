"""AIO `init` command — scaffold a new project directory."""
# NOTE: NO `from __future__ import annotations` in this file.
# Typer relies on runtime type introspection; postponed evaluation breaks it.

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
import yaml

from aio._log import get_logger
from aio._validators import yaml_safe_load
from aio.exceptions import AIOError, ConfigError
from aio.themes.loader import load_registry

_log = get_logger(__name__)

SUPPORTED_AGENTS: frozenset[str] = frozenset(
    {"claude", "gemini", "copilot", "windsurf", "devin", "chatgpt", "cursor", "generic"}
)

# ---------------------------------------------------------------------------
# ProjectConfig
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProjectConfig:
    """Immutable project configuration loaded from .aio/config.yaml."""

    agent: str
    theme: str = "default"
    enrich: bool = False
    serve_port: int = 8000
    output_dir: str = "build"

    def __post_init__(self) -> None:
        # Resolve "default" alias → "minimal" before validation
        if self.theme == "default":
            object.__setattr__(self, "theme", "minimal")
        # Validate agent
        if self.agent not in SUPPORTED_AGENTS:
            raise ConfigError(
                f"Unknown agent '{self.agent}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_AGENTS))}"
            )

    @classmethod
    def load(cls, dir_path: str | Path) -> "ProjectConfig":
        """Load ProjectConfig from {dir_path}/config.yaml.

        Raises ConfigError on missing file or invalid agent.
        """
        config_path = Path(dir_path) / "config.yaml"
        if not config_path.is_file():
            raise ConfigError(f"Config file not found: {config_path}")
        content = config_path.read_text(encoding="utf-8")
        data = yaml_safe_load(content, source=str(config_path))
        _log.debug("Loaded config from %s: %s", config_path, data)
        return cls(
            agent=str(data.get("agent", "claude")),
            theme=str(data.get("theme", "default")),
            enrich=bool(data.get("enrich", False)),
            serve_port=int(data.get("serve_port", 8000)),
            output_dir=str(data.get("output_dir", "build")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dict (all fields, post-alias)."""
        return {
            "agent": self.agent,
            "theme": self.theme,
            "enrich": self.enrich,
            "serve_port": self.serve_port,
            "output_dir": self.output_dir,
        }


# ---------------------------------------------------------------------------
# Slides template
# ---------------------------------------------------------------------------

SLIDES_MD_TEMPLATE = """\
---
title: {title}
agent: {agent}
theme: {theme}
---

# Welcome

<!-- @layout: hero-title -->
<!-- @title: Welcome to {title} -->
<!-- @subtitle: Your AI-native presentation -->

---

# Getting Started

<!-- @layout: content -->

Add your content here. Use `<!-- @layout: layout-name -->` to select layouts.

Available layouts: hero-title, content, two-column, three-column, full-image,
code, quote, timeline, comparison, gallery, data, icon-grid, narrative, diagram,
custom, interactive.
"""

# ---------------------------------------------------------------------------
# Project structure builder
# ---------------------------------------------------------------------------


def _create_project_structure(
    name: str,
    path: Path,
    config: ProjectConfig,
    dry_run: bool,
) -> None:
    """Create the full .aio/ project scaffold.

    If dry_run=True, logs planned structure to stderr but does not write anything.
    """
    dirs = [
        path / ".aio" / "themes",
        path / "assets",
        path / "build",
    ]
    files: dict[Path, str] = {}

    # config.yaml
    config_data = config.to_dict()
    files[path / ".aio" / "config.yaml"] = yaml.dump(config_data, default_flow_style=False)

    # meta.json
    meta = {
        "project_name": name,
        "created_at": datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": "0.1.0",
    }
    files[path / ".aio" / "meta.json"] = json.dumps(meta, indent=2)

    # per-project themes/registry.json — only the selected theme
    global_registry = load_registry()
    theme_entry = next((t for t in global_registry if t["id"] == config.theme), None)
    if theme_entry is None:
        # fallback to minimal if theme somehow missing
        theme_entry = {"id": config.theme, "name": config.theme.capitalize()}
    files[path / ".aio" / "themes" / "registry.json"] = json.dumps([theme_entry], indent=2)

    # slides.md
    files[path / "slides.md"] = SLIDES_MD_TEMPLATE.format(
        title=name,
        agent=config.agent,
        theme=config.theme,
    )

    if dry_run:
        _log.info("DRY RUN — would create project '%s' at %s", name, path)
        for d in dirs:
            _log.info("  mkdir  %s", d)
        for f in files:
            _log.info("  write  %s (%d bytes)", f, len(files[f]))
        return

    # Actually create
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    for file_path, content in files.items():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        _log.debug("Wrote %s", file_path)

    _log.info("Project '%s' created at %s", name, path)


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------

app = typer.Typer()


@app.command()
def init(
    name: str = typer.Argument(None, help="Project name (defaults to current directory name)"),
    theme: str = typer.Option("minimal", "--theme", "-t", help="Theme ID (must exist in registry)"),
    agent: str = typer.Option("claude", "--agent", "-a", help="AI agent (claude, gemini, copilot, windsurf, devin, chatgpt, cursor, generic)"),  # noqa: E501
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing project"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show planned structure without creating files"),
) -> None:
    """Create a new AIO project."""
    if name is None:
        name = Path.cwd().name

    # Validate agent before touching filesystem
    if agent not in SUPPORTED_AGENTS:
        msg = f"Unknown agent '{agent}'. Supported: {', '.join(sorted(SUPPORTED_AGENTS))}"
        _log.error("%s", msg)
        typer.echo(msg, err=True)
        raise typer.Exit(code=1)

    project_path = Path.cwd() / name

    if not dry_run and (project_path / ".aio").exists() and not force:
        _log.error(
            "Project '%s' already exists at %s. Use --force to overwrite.",
            name,
            project_path,
        )
        raise typer.Exit(code=1)

    try:
        config = ProjectConfig(agent=agent, theme=theme)
    except ConfigError as exc:
        _log.error("%s", exc)
        raise typer.Exit(code=1)

    try:
        _create_project_structure(name, project_path, config, dry_run)
    except AIOError as exc:
        _log.error("%s", exc)
        raise typer.Exit(code=1)

    if dry_run:
        typer.echo(f"[dry-run] Would initialize project '{name}' with agent={agent}, theme={theme}")
    else:
        typer.echo(str(project_path.resolve()))
        _log.info("✓ Project '%s' initialized with '%s' agent and '%s' theme", name, agent, theme)
