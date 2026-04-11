"""AIO `serve` command stub — hot-reload server implementation is M1."""
# NOTE: NO `from __future__ import annotations` — breaks Typer runtime introspection
from pathlib import Path

import typer

from aio._log import get_logger

_log = get_logger(__name__)

app = typer.Typer()


@app.command()
def serve(
    input: Path = typer.Argument(Path("slides.md"), help="Input slides.md path"),
    port: int = typer.Option(8000, "--port", "-p", help="Dev server port"),
    host: str = typer.Option("127.0.0.1", "--host", help="Dev server host"),
    no_reload: bool = typer.Option(False, "--no-reload", help="Disable hot reload"),
) -> None:
    """Start dev server with hot reload."""
    # Config auto-load (US5 — T057)
    try:
        from aio._utils import find_aio_dir
        from aio.commands.init import ProjectConfig

        aio_dir = find_aio_dir(input.parent if input.parent != Path(".") else Path.cwd())
        cfg = ProjectConfig.load(aio_dir)
        _log.debug("Config loaded: agent=%s, theme=%s", cfg.agent, cfg.theme)
    except Exception as exc:
        _log.debug("Could not load project config: %s", exc)

    _log.info("serve: not yet implemented (planned for M1)")
    _log.info("Command complete")
