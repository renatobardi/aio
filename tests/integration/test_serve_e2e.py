"""Integration tests for the serve command hot-reload server (T052, T059).

SSE streaming tests start a REAL uvicorn server in a background thread with a real
TCP socket. Both httpx ASGITransport and Starlette TestClient buffer the entire
response body before returning, making them unsuitable for infinite SSE streams.
With a real TCP connection, r.close() sends a FIN packet which uvicorn forwards as
http.disconnect to the ASGI app, allowing the SSE generator to stop cleanly.
"""

from __future__ import annotations

import asyncio
import socket
import threading
import time
from pathlib import Path

import pytest

FIXTURE_SLIDES = Path(__file__).parent.parent / "fixtures" / "slides" / "sample_all_layouts.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _free_port() -> int:
    """Return an OS-assigned free TCP port."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _bind_port(port: int) -> socket.socket:
    """Bind a port and keep it occupied; caller must close()."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", port))
    s.listen(1)
    return s


# ---------------------------------------------------------------------------
# App factory tests
# ---------------------------------------------------------------------------

def test_create_app_returns_starlette_app() -> None:
    from aio.commands.serve import create_app
    from starlette.applications import Starlette

    app = create_app(FIXTURE_SLIDES)
    assert isinstance(app, Starlette)


def _asgi_client(app):
    """Return an httpx.AsyncClient wired to the given ASGI app (non-streaming only)."""
    import httpx
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    )


@pytest.fixture()
def live_server(tmp_path):
    """Start a real uvicorn server in a background thread for SSE streaming tests.

    Returns the base URL (e.g. "http://127.0.0.1:PORT").
    The server uses a short SSE ping interval so SSE generator cleanup is fast.
    """
    import uvicorn

    import aio.commands.serve as serve_mod
    from aio.commands.serve import create_app

    # Short ping so SSE generator exits quickly after client disconnects
    original_ping = serve_mod._SSE_PING_INTERVAL
    serve_mod._SSE_PING_INTERVAL = 0.05

    port = _free_port()
    app = create_app(FIXTURE_SLIDES)

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", loop="asyncio")
    server = uvicorn.Server(config)

    t = threading.Thread(target=server.run, daemon=True)
    t.start()

    # Wait up to 5 s for the server to accept connections
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.05)
    else:
        pytest.fail("Live server did not start within 5 s")

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    t.join(timeout=5.0)
    serve_mod._SSE_PING_INTERVAL = original_ping


@pytest.mark.asyncio
async def test_get_root_returns_200_html() -> None:
    from aio.commands.serve import create_app

    app = create_app(FIXTURE_SLIDES)
    async with _asgi_client(app) as client:
        r = await client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


@pytest.mark.asyncio
async def test_get_root_contains_reveal_js() -> None:
    from aio.commands.serve import create_app

    app = create_app(FIXTURE_SLIDES)
    async with _asgi_client(app) as client:
        r = await client.get("/")
    html = r.text
    assert "reveal" in html.lower() or "Reveal" in html


@pytest.mark.asyncio
async def test_get_root_contains_eventsource_script() -> None:
    from aio.commands.serve import create_app

    app = create_app(FIXTURE_SLIDES)
    async with _asgi_client(app) as client:
        r = await client.get("/")
    assert "EventSource" in r.text


def test_get_sse_endpoint_returns_200_stream(live_server: str) -> None:
    """SSE endpoint returns 200 text/event-stream with real TCP socket."""
    import httpx

    with httpx.Client() as client:
        with client.stream("GET", f"{live_server}/__sse__") as r:
            assert r.status_code == 200
            assert "text/event-stream" in r.headers.get("content-type", "")
            for chunk in r.iter_text():
                if chunk.strip():
                    break  # Got first event; close connection cleanly


def test_get_sse_first_event_is_connected(live_server: str) -> None:
    """SSE stream first data event must be {"type": "connected"} (real TCP)."""
    import json

    import httpx

    with httpx.Client() as client:
        with client.stream("GET", f"{live_server}/__sse__") as r:
            for line in r.iter_lines():
                line = line.strip()
                if line.startswith("data:"):
                    payload = json.loads(line[5:].strip())
                    assert payload["type"] == "connected"
                    return  # Pass — got the connected event
    pytest.fail("SSE stream closed without emitting a data event")


# ---------------------------------------------------------------------------
# Port collision detection (T059)
# ---------------------------------------------------------------------------

def test_port_collision_exits_2(tmp_path: Path) -> None:
    """serve() must exit with code 2 when the port is already bound."""
    import typer
    from typer.testing import CliRunner

    from aio.commands.serve import app as serve_app

    port = _free_port()
    occupied = _bind_port(port)
    try:
        runner = CliRunner()
        result = runner.invoke(serve_app, [str(FIXTURE_SLIDES), "--port", str(port)])
        assert result.exit_code == 2, f"Expected exit 2, got {result.exit_code}: {result.output}"
    finally:
        occupied.close()


def test_host_0000_accepted(tmp_path: Path) -> None:
    """--host 0.0.0.0 must not raise an error before binding."""
    import typer
    from typer.testing import CliRunner

    from aio.commands.serve import app as serve_app

    port = _free_port()
    occupied = _bind_port(port)
    try:
        runner = CliRunner()
        # Port already taken → exits 2, but host option parsed correctly (no parse error)
        result = runner.invoke(serve_app, [str(FIXTURE_SLIDES), "--host", "0.0.0.0", "--port", str(port)])
        # Exit 2 means collision detected — host was accepted (not exit 9 / usage error)
        assert result.exit_code in (0, 2)
    finally:
        occupied.close()
