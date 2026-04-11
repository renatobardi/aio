"""Tests for logging infrastructure (US6)."""
from __future__ import annotations

import logging

from typer.testing import CliRunner

runner = CliRunner()


def _app():
    from aio.cli import app

    return app


class TestLoggingLevels:
    """Logging levels are correctly set by flags and env vars."""

    def teardown_method(self) -> None:
        # Reset logger state between tests
        root = logging.getLogger("aio")
        root.handlers.clear()
        root.setLevel(logging.NOTSET)

    def test_default_run_no_debug_lines(self, capfd) -> None:
        from aio._log import setup_logging

        setup_logging(logging.INFO)
        log = logging.getLogger("aio.test")
        log.debug("this debug line should not appear")
        log.info("this info line should appear")

        captured = capfd.readouterr()
        assert "debug line should not appear" not in captured.err

    def test_verbose_flag_shows_debug_lines(self, capfd) -> None:
        from aio._log import setup_logging

        setup_logging(logging.DEBUG)
        log = logging.getLogger("aio.test")
        log.debug("debug message")

        captured = capfd.readouterr()
        assert "debug message" in captured.err

    def test_env_var_sets_debug_level(self, monkeypatch, capfd) -> None:
        monkeypatch.setenv("AIO_LOG_LEVEL", "DEBUG")
        from aio._log import setup_logging

        setup_logging()  # uses default INFO, but env var overrides

        log = logging.getLogger("aio.test")
        log.debug("env debug message")

        captured = capfd.readouterr()
        assert "env debug message" in captured.err

    def test_sensitive_api_key_masked(self, capfd) -> None:
        from aio._log import setup_logging

        setup_logging(logging.DEBUG)
        log = logging.getLogger("aio.test")
        log.debug("API key: abcdef1234567890abcdef1234567890")

        captured = capfd.readouterr()
        assert "abcdef1234567890abcdef1234567890" not in captured.err
        assert "***" in captured.err

    def test_bearer_token_masked(self, capfd) -> None:
        from aio._log import setup_logging

        setup_logging(logging.DEBUG)
        log = logging.getLogger("aio.test")
        log.debug("Token: Bearer my-secret-token-xyz")

        captured = capfd.readouterr()
        assert "my-secret-token-xyz" not in captured.err
        assert "Bearer ***" in captured.err

    def test_setup_logging_is_idempotent(self, capfd) -> None:
        from aio._log import setup_logging

        setup_logging(logging.INFO)
        setup_logging(logging.INFO)
        setup_logging(logging.INFO)

        root = logging.getLogger("aio")
        assert len(root.handlers) == 1  # No duplicate handlers

    def test_logging_writes_to_stderr_not_stdout(self, capfd) -> None:
        from aio._log import setup_logging

        setup_logging(logging.INFO)
        log = logging.getLogger("aio.test")
        log.info("goes to stderr")

        captured = capfd.readouterr()
        assert "goes to stderr" in captured.err
        assert "goes to stderr" not in captured.out


class TestCLILoggingIntegration:
    """CLI --verbose and --quiet flags wire logging correctly."""

    def setup_method(self) -> None:
        # Reset logger state before each test
        root = logging.getLogger("aio")
        root.handlers.clear()
        root.setLevel(logging.NOTSET)

    def test_at_least_1_line_on_command_completion(self) -> None:
        # CliRunner captures its own output — check result.output (mixes stdout+stderr)
        result = runner.invoke(_app(), ["theme", "list"])
        # At minimum the table or log line should appear
        assert len(result.output.strip()) > 0, "Expected at least 1 output line from theme list"
