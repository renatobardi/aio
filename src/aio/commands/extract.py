"""AIO `extract` command stub — web scraper to DESIGN.md (M1)."""

# NOTE: NO from __future__ import annotations — breaks Typer runtime introspection
import typer

from aio._log import get_logger

_log = get_logger(__name__)

app = typer.Typer()


@app.command()
def extract(
    url: str = typer.Argument(..., help="URL to scrape for design tokens"),
    output: str = typer.Option("DESIGN.md", "--output", "-o", help="Output DESIGN.md path"),
    sections: str = typer.Option(None, "--sections", help="Comma-separated sections to extract"),
) -> None:
    """Web scraper → DESIGN.md for new theme creation."""
    _log.info("extract: not yet implemented (planned for M1)")
    _log.info("Command complete")
