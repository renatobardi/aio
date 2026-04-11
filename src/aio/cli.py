# NOTE: NO `from __future__ import annotations` in this file.
# Typer relies on runtime type introspection; postponed evaluation breaks it.
"""AIO root CLI — `aio` entry point."""
import importlib.metadata
import logging

import typer

from aio._log import setup_logging
from aio.commands.build import build
from aio.commands.commands import app as commands_app
from aio.commands.extract import extract

# Import command functions directly (not as sub-Typers for leaf commands)
from aio.commands.init import init
from aio.commands.serve import serve
from aio.commands.theme import app as theme_app

app = typer.Typer(
    name="aio",
    help="AIO — AI-native presentation generator",
    add_completion=False,
)

# Leaf commands registered directly
app.command("init")(init)
app.command("build")(build)
app.command("serve")(serve)
app.command("extract")(extract)

# Group commands (have subcommands)
app.add_typer(theme_app, name="theme")
app.add_typer(commands_app, name="commands")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context = typer.Option(None, hidden=True),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable DEBUG logging to stderr"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Only show ERROR and above"),
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
) -> None:
    """AIO — AI-native presentation generator."""
    if version:
        v = importlib.metadata.version("aio")
        typer.echo(f"aio {v}")
        raise typer.Exit()

    # quiet wins over verbose (FR-131/FR-112a)
    if quiet:
        setup_logging(logging.ERROR)
    elif verbose:
        setup_logging(logging.DEBUG)
    else:
        setup_logging(logging.INFO)
