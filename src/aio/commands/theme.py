"""AIO `theme` command group — list, validate, and manage themes."""
# NOTE: NO `from __future__ import annotations` in this file.
# Typer relies on runtime type introspection; postponed evaluation breaks it.

import typer
from rich.console import Console
from rich.table import Table

from aio._log import get_logger
from aio.themes.loader import load_registry
from aio.themes.validator import validate_theme

_log = get_logger(__name__)
console = Console(stderr=False)

app = typer.Typer(name="theme", help="Theme management (list, validate, search, info, use, show, create)")


@app.command("list")
def list_themes() -> None:
    """List all available themes."""
    registry = load_registry()
    table = Table(title="Available Themes")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Tags")
    table.add_column("Source")
    for entry in registry:
        table.add_row(
            entry.get("id", ""),
            entry.get("name", ""),
            ", ".join(entry.get("tags", [])),
            entry.get("source", ""),
        )
    console.print(table)
    _log.info("Command complete")


@app.command("validate")
def validate(
    theme_id: str = typer.Argument(..., help="Theme ID to validate"),
) -> None:
    """Validate a theme's DESIGN.md against the 11-section schema."""
    errors = validate_theme(theme_id)
    if errors:
        for err in errors:
            _log.error("%s", err)
        typer.echo(f"✗ Theme '{theme_id}' has {len(errors)} validation error(s).", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"✓ Theme '{theme_id}' is valid.")
    _log.info("Command complete")


# --- Stub subcommands (M1+) ---

@app.command("search")
def search(
    query: str = typer.Argument(..., help="Search query"),
) -> None:
    """Search themes by name or tags."""
    _log.info("theme search: not yet implemented")
    _log.info("Command complete")


@app.command("info")
def info(
    theme_id: str = typer.Argument(..., help="Theme ID"),
) -> None:
    """Show detailed theme information."""
    _log.info("theme info: not yet implemented")
    _log.info("Command complete")


@app.command("use")
def use(
    theme_id: str = typer.Argument(..., help="Theme ID to activate"),
) -> None:
    """Set the active theme for the current project."""
    _log.info("theme use: not yet implemented")
    _log.info("Command complete")


@app.command("show")
def show(
    theme_id: str = typer.Argument(..., help="Theme ID to preview"),
) -> None:
    """Preview a theme in the browser."""
    _log.info("theme show: not yet implemented")
    _log.info("Command complete")


@app.command("create")
def create(
    name: str = typer.Argument(..., help="New theme name"),
) -> None:
    """Create a new theme scaffold."""
    _log.info("theme create: not yet implemented")
    _log.info("Command complete")
