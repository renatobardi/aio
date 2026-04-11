"""Tests for the root CLI (US2)."""
from __future__ import annotations

import logging

from typer.testing import CliRunner

runner = CliRunner()


def _app():
    from aio.cli import app

    return app


class TestHelpOutput:
    """aio --help shows 6 subcommands."""

    def test_help_shows_6_subcommands(self) -> None:
        result = runner.invoke(_app(), ["--help"])
        assert result.exit_code == 0
        output = result.output
        # All 6 subcommands must be present
        for cmd in ("init", "build", "serve", "theme", "extract", "commands"):
            assert cmd in output, f"Missing subcommand '{cmd}' in --help output"

    def test_help_exit_code_0(self) -> None:
        result = runner.invoke(_app(), ["--help"])
        assert result.exit_code == 0

    def test_build_help_shows_flags(self) -> None:
        result = runner.invoke(_app(), ["build", "--help"])
        assert result.exit_code == 0
        output = result.output
        for flag in ("--output", "--theme", "--enrich"):
            assert flag in output, f"Missing flag '{flag}' in build --help"

    def test_theme_help_shows_subcommands(self) -> None:
        result = runner.invoke(_app(), ["theme", "--help"])
        assert result.exit_code == 0
        for sub in ("list", "validate"):
            assert sub in result.output, f"Missing '{sub}' in theme --help"


class TestVersionFlag:
    """aio --version prints version and exits 0."""

    def test_version_prints_aio_version(self) -> None:
        result = runner.invoke(_app(), ["--version"])
        assert result.exit_code == 0
        assert "aio" in result.output.lower() or "0.1.0" in result.output


class TestVerboseFlag:
    """--verbose wires DEBUG logging; --quiet wires ERROR."""

    def test_verbose_sets_debug_level(self, capfd) -> None:
        runner.invoke(_app(), ["--verbose", "theme", "list"])
        # After invoking, root aio logger should have been set to DEBUG
        # We check via the logging level of the root aio logger
        aio_logger = logging.getLogger("aio")
        assert aio_logger.level <= logging.DEBUG

    def test_quiet_sets_error_level(self) -> None:
        runner.invoke(_app(), ["--quiet", "theme", "list"])
        aio_logger = logging.getLogger("aio")
        assert aio_logger.level == logging.ERROR

    def test_quiet_wins_over_verbose(self) -> None:
        runner.invoke(_app(), ["--quiet", "--verbose", "theme", "list"])
        aio_logger = logging.getLogger("aio")
        assert aio_logger.level == logging.ERROR
