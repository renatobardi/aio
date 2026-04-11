"""AIO `serve` command — Starlette ASGI hot-reload server.

Set AIO_SSE_PING_INTERVAL (seconds, float) to override the SSE keep-alive ping
interval. Defaults to 15s in production. Tests set it to ~0.05s so the stream
yields a ping chunk quickly and then exits cleanly after the client disconnects.


Architecture:
  - Starlette ASGI app with two routes: GET / and GET /__sse__
  - watchdog Observer watches the source .md file for modifications
  - Per-connection asyncio.Queue receives HotReloadEvent and streams as SSE
  - uvicorn runs the app; SIGINT triggers graceful shutdown

NOTE: NO `from __future__ import annotations` — breaks Typer runtime introspection.
"""

import asyncio
import json
import os
import signal
import socket
import time
from collections.abc import Callable
from pathlib import Path

import typer
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, StreamingResponse
from starlette.routing import Route

from aio._log import get_logger
from aio.composition.metadata import HotReloadEvent

# Configurable keep-alive interval — override in tests via AIO_SSE_PING_INTERVAL env var
_SSE_PING_INTERVAL: float = float(os.environ.get("AIO_SSE_PING_INTERVAL", "15.0"))

_log = get_logger(__name__)

app = typer.Typer()

# ---------------------------------------------------------------------------
# SSE broadcast registry — list of queues, one per connected browser tab
# ---------------------------------------------------------------------------
_connections: list[asyncio.Queue[HotReloadEvent]] = []


def _broadcast(event: HotReloadEvent) -> None:
    """Push an event to all connected SSE clients (called from watchdog thread)."""
    for q in list(_connections):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            pass


# ---------------------------------------------------------------------------
# Watchdog file handler
# ---------------------------------------------------------------------------


class _FileModifiedHandler:
    """Minimal watchdog-compatible event handler."""

    def __init__(self, source: Path, loop: asyncio.AbstractEventLoop) -> None:
        self._source = source
        self._loop = loop

    def dispatch(self, event: object) -> None:
        src = getattr(event, "src_path", "")
        if Path(src).resolve() == self._source.resolve():
            reload_event = HotReloadEvent(
                event_type="reload",
                message=f"File changed: {self._source.name}",
                source_path=self._source,
                timestamp=time.time(),
            )
            self._loop.call_soon_threadsafe(_broadcast, reload_event)


# ---------------------------------------------------------------------------
# ASGI app factory
# ---------------------------------------------------------------------------


def create_app(source: Path, build_fn: Callable[[], str] | None = None) -> Starlette:
    """Create and return the Starlette ASGI app.

    Args:
        source: Path to the input slides.md file.
        build_fn: Optional callable returning built HTML string. If None, the
                  default build_pipeline is used.
    """
    if build_fn is None:
        from aio.commands.build import build_pipeline as _bp

        def _default_build() -> str:
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
                out = Path(f.name)
            _bp(source, output=out, theme_id="minimal", serve_mode=True)
            html = out.read_text(encoding="utf-8")
            out.unlink(missing_ok=True)
            return html

        build_fn = _default_build

    # Build once at startup; cache result
    _cache: dict[str, str] = {}

    def _get_html() -> str:
        if "html" not in _cache:
            try:
                _cache["html"] = build_fn()
            except Exception as exc:
                _log.error("Build failed: %s", exc)
                _cache["html"] = f"<!DOCTYPE html><html><body><pre>Build error: {exc}</pre></body></html>"
        return _cache["html"]

    async def _root(request: Request) -> HTMLResponse:
        return HTMLResponse(_get_html())

    async def _sse(request: Request) -> StreamingResponse:
        q: asyncio.Queue[HotReloadEvent] = asyncio.Queue(maxsize=32)
        _connections.append(q)

        async def _event_stream():
            # Send connected confirmation immediately
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            try:
                while True:
                    # asyncio.timeout (Python 3.11+) is properly cancellable via
                    # GeneratorExit/CancelledError — unlike asyncio.wait_for which
                    # creates an internal task that survives generator closure.
                    event = None
                    try:
                        async with asyncio.timeout(_SSE_PING_INTERVAL):
                            event = await q.get()
                    except TimeoutError:
                        # Keep-alive ping so the connection doesn't time out
                        yield ": ping\n\n"
                        continue
                    payload = {
                        "type": event.event_type,
                        "message": event.message,
                        "timestamp": event.timestamp,
                    }
                    # Invalidate HTML cache on reload so next GET / rebuilds
                    if event.event_type == "reload":
                        _cache.pop("html", None)
                    yield f"data: {json.dumps(payload)}\n\n"
            except (asyncio.CancelledError, GeneratorExit):
                pass
            finally:
                if q in _connections:
                    _connections.remove(q)

        return StreamingResponse(
            _event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    return Starlette(
        routes=[
            Route("/", _root),
            Route("/__sse__", _sse),
        ]
    )


# ---------------------------------------------------------------------------
# Port collision check
# ---------------------------------------------------------------------------


def _port_in_use(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.1):
            return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Typer CLI command
# ---------------------------------------------------------------------------


@app.command()
def serve(
    input: Path = typer.Argument(Path("slides.md"), help="Input slides.md path"),
    port: int = typer.Option(8000, "--port", "-p", help="Dev server port"),
    host: str = typer.Option("127.0.0.1", "--host", help="Dev server host"),
    no_reload: bool = typer.Option(False, "--no-reload", help="Disable hot reload"),
    open_browser: bool = typer.Option(False, "--open", help="Open browser after start"),
) -> None:
    """Start dev server with SSE hot reload."""
    import uvicorn
    from watchdog.observers import Observer

    if _port_in_use(host, port):
        _log.error("Port %d is already in use", port)
        raise typer.Exit(code=2)

    if not input.exists():
        _log.error("Input file not found: %s", input)
        raise typer.Exit(code=3)

    _log.info("Starting serve on http://%s:%d", host, port)

    starlette_app = create_app(input)

    # --- watchdog setup ---
    observer = None  # type: ignore[var-annotated]
    if not no_reload:
        handler = _FileModifiedHandler(input, loop=asyncio.get_event_loop())

        from watchdog.events import FileSystemEventHandler

        class _WatchdogBridge(FileSystemEventHandler):
            def on_modified(self, event: object) -> None:
                handler.dispatch(event)

        observer = Observer()
        watch_dir = str(input.parent.resolve())
        observer.schedule(_WatchdogBridge(), watch_dir, recursive=False)
        observer.start()
        _log.debug("watchdog observer started on %s", watch_dir)

    # --- uvicorn config ---
    config = uvicorn.Config(
        starlette_app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)

    # --- SIGINT handler ---
    def _shutdown(signum: int, frame: object) -> None:
        _log.info("Shutting down serve...")
        server.should_exit = True
        if observer is not None:
            observer.stop()
            observer.join(timeout=2.0)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _shutdown)

    if open_browser:
        import webbrowser

        webbrowser.open(f"http://{host}:{port}")

    try:
        server.run()
    finally:
        if observer is not None and observer.is_alive():
            observer.stop()
            observer.join(timeout=2.0)
