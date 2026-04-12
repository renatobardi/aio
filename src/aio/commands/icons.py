"""AIO `icons` command group — discover bundled Lucide icons."""
# NOTE: NO `from __future__ import annotations` in this file.
# Typer relies on runtime type introspection; postponed evaluation breaks it.


import typer
from rich.console import Console

from aio._log import get_logger
from aio.visuals.svg.icons import list_icons

_log = get_logger(__name__)
console = Console(stderr=False)

app = typer.Typer(name="icons", help="Discover bundled Lucide icon library")


@app.command("list")
def list_command(
    filter: str | None = typer.Option(None, "--filter", help="Filter by tag substring (case-insensitive)"),
    count: bool = typer.Option(False, "--count", help="Print only the total count"),
) -> None:
    """List all available icons in the bundled Lucide library."""
    icons = list_icons(filter=filter)

    if count:
        console.print(len(icons))
        return

    for name, tags in icons:
        console.print(f"{name:<20} Tags: {', '.join(tags)}")
