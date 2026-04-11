"""Integration tests for `aio commands` subcommands (US7)."""
from __future__ import annotations

from typer.testing import CliRunner

runner = CliRunner()


def _app():
    from aio.cli import app

    return app


class TestCommandsListIntegration:
    """aio commands list shows 7 commands."""

    def test_list_shows_7_commands(self) -> None:
        result = runner.invoke(_app(), ["commands", "list"])
        assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"
        output = result.output
        for cmd in ("outline", "generate", "refine", "visual", "theme", "extract", "build"):
            assert cmd in output, f"Missing command '{cmd}' in output"

    def test_list_shows_descriptions(self) -> None:
        result = runner.invoke(_app(), ["commands", "list"])
        assert result.exit_code == 0
        # Output should have at least 7 non-empty lines with content
        lines = [ln for ln in result.output.strip().splitlines() if ln.strip()]
        assert len(lines) >= 7


class TestCommandsOutlineIntegration:
    """aio commands outline returns non-empty prompt."""

    def test_outline_claude_non_empty(self) -> None:
        result = runner.invoke(_app(), ["commands", "outline", "--agent", "claude"])
        assert result.exit_code == 0
        assert len(result.output.strip()) > 0

    def test_outline_8_agents_produce_output(self) -> None:
        agents = ["claude", "gemini", "copilot", "windsurf", "devin", "chatgpt", "cursor", "generic"]
        outputs = {}
        for agent in agents:
            result = runner.invoke(_app(), ["commands", "outline", "--agent", agent])
            assert result.exit_code == 0, f"Agent '{agent}' failed: {result.output}"
            outputs[agent] = result.output.strip()
            assert len(outputs[agent]) > 0, f"Agent '{agent}' returned empty output"

    def test_outputs_differ_between_agents(self) -> None:
        agents = ["claude", "gemini", "generic"]
        outputs = set()
        for agent in agents:
            result = runner.invoke(_app(), ["commands", "outline", "--agent", agent])
            outputs.add(result.output.strip())
        assert len(outputs) > 1, "All agents produce identical output"
