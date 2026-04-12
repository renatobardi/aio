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
from collections.abc import AsyncGenerator, Callable
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
    """Minimal watchdog-compatible event handler.

    The event loop is injected via set_loop() from within the running async context
    (Starlette on_startup), not at construction time. This avoids calling
    asyncio.get_event_loop() before uvicorn has created its own loop (Python 3.12+ crash).
    """

    def __init__(self, source: Path, extra_dirs: list[Path] | None = None) -> None:
        self._source = source
        self._extra_dirs: list[Path] = [d.resolve() for d in (extra_dirs or [])]
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Called from Starlette on_startup once the event loop is running."""
        self._loop = loop

    def dispatch(self, event: object) -> None:
        if self._loop is None:
            return
        src = getattr(event, "src_path", "")
        src_path = Path(src).resolve()
        triggered = src_path == self._source.resolve() or any(
            str(src_path).startswith(str(d) + "/") for d in self._extra_dirs
        )
        if triggered:
            label = src_path.name if src_path != self._source.resolve() else self._source.name
            reload_event = HotReloadEvent(
                event_type="reload",
                message=f"File changed: {label}",
                source_path=self._source,
                timestamp=time.time(),
            )
            self._loop.call_soon_threadsafe(_broadcast, reload_event)


# ---------------------------------------------------------------------------
# ASGI app factory
# ---------------------------------------------------------------------------


def create_app(
    source: Path,
    build_fn: Callable[[], str] | None = None,
    file_handler: _FileModifiedHandler | None = None,
) -> Starlette:
    """Create and return the Starlette ASGI app.

    Args:
        source: Path to the input slides.md file.
        build_fn: Optional callable returning built HTML string. If None, the
                  default build_pipeline is used.
        file_handler: Optional _FileModifiedHandler whose loop is set on startup.
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

        async def _event_stream() -> AsyncGenerator[str, None]:
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

    async def _on_startup() -> None:
        if file_handler is not None:
            file_handler.set_loop(asyncio.get_running_loop())

    return Starlette(
        routes=[
            Route("/", _root),
            Route("/__sse__", _sse),
        ],
        on_startup=[_on_startup],
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

    original_port = port
    while _port_in_use(host, port):
        if port - original_port >= 10:
            _log.error("Could not find a free port in range %d-%d", original_port, port)
            raise typer.Exit(code=2)
        port += 1
    if port != original_port:
        _log.info("Port %d in use — using port %d instead", original_port, port)

    if not input.exists():
        _log.error("Input file not found: %s", input)
        raise typer.Exit(code=3)

    _log.info("Starting serve on http://%s:%d", host, port)

    # --- watchdog setup ---
    # Locate .aio/ so config.yaml and themes/* changes also trigger reload
    _aio_dir: Path | None = None
    if not no_reload:
        from aio._utils import find_aio_dir
        from aio.exceptions import AIOError

        try:
            _aio_dir = find_aio_dir(input.parent)
        except (FileNotFoundError, AIOError):
            pass

    extra_dirs = [_aio_dir] if _aio_dir is not None else []
    handler = _FileModifiedHandler(input, extra_dirs=extra_dirs) if not no_reload else None
    starlette_app = create_app(input, file_handler=handler)

    observer = None
    if handler is not None:
        from watchdog.events import FileSystemEventHandler

        _handler = handler  # narrow type for mypy inside nested class

        class _WatchdogBridge(FileSystemEventHandler):
            def on_modified(self, event: object) -> None:
                _handler.dispatch(event)

        observer = Observer()
        watch_dir = str(input.parent.resolve())
        observer.schedule(_WatchdogBridge(), watch_dir, recursive=False)  # type: ignore[no-untyped-call]
        if _aio_dir is not None:
            observer.schedule(_WatchdogBridge(), str(_aio_dir.resolve()), recursive=True)  # type: ignore[no-untyped-call]
            _log.debug("watchdog also observing .aio/ at %s", _aio_dir)
        observer.start()  # type: ignore[no-untyped-call]
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
            observer.stop()  # type: ignore[no-untyped-call]
            observer.join(timeout=2.0)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _shutdown)

    if open_browser:
        import webbrowser

        webbrowser.open(f"http://{host}:{port}")  # NOSONAR: intentional HTTP for local dev server

    try:
        server.run()
    finally:
        if observer is not None and observer.is_alive():
            observer.stop()  # type: ignore[no-untyped-call]
            observer.join(timeout=2.0)
