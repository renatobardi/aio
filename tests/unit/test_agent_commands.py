"""Tests for agent command template system (US7)."""
from __future__ import annotations

import socket


class TestListCommands:
    """list_commands() returns all 7 commands."""

    def test_returns_7_tuples(self) -> None:
        from aio.agents.prompts import list_commands

        commands = list_commands()
        assert len(commands) == 7

    def test_all_7_names_present(self) -> None:
        from aio.agents.prompts import list_commands

        names = {name for name, _ in list_commands()}
        expected = {"outline", "generate", "refine", "visual", "theme", "extract", "build"}
        assert names == expected

    def test_each_command_has_description(self) -> None:
        from aio.agents.prompts import list_commands

        for name, desc in list_commands():
            assert isinstance(desc, str) and len(desc) > 0, f"Command '{name}' has empty description"


class TestLoadAgentTemplate:
    """load_agent_template() returns correct content for each agent/command."""

    def test_claude_outline_has_system_prompt(self) -> None:
        from aio.agents.prompts import load_agent_template

        tmpl = load_agent_template("claude", "outline")
        assert tmpl.has_system_prompt is True

    def test_gemini_outline_no_system_prompt(self) -> None:
        from aio.agents.prompts import load_agent_template

        tmpl = load_agent_template("gemini", "outline")
        assert tmpl.has_system_prompt is False

    def test_all_8_agents_return_non_empty_content(self) -> None:
        from aio.agents.prompts import load_agent_template

        agents = ["claude", "gemini", "copilot", "windsurf", "devin", "chatgpt", "cursor", "generic"]
        for agent in agents:
            tmpl = load_agent_template(agent, "outline")
            assert len(tmpl.content) > 0, f"Agent '{agent}' returned empty content for outline"

    def test_all_7_commands_work_for_claude(self) -> None:
        from aio.agents.prompts import load_agent_template

        commands = ["outline", "generate", "refine", "visual", "theme", "extract", "build"]
        for cmd in commands:
            tmpl = load_agent_template("claude", cmd)
            assert len(tmpl.content) > 0

    def test_outline_content_under_2000_chars(self) -> None:
        from aio.agents.prompts import load_agent_template

        tmpl = load_agent_template("claude", "outline")
        assert len(tmpl.content) < 2000, f"Outline template is {len(tmpl.content)} chars — must be < 2000"

    def test_unknown_agent_raises_value_error(self) -> None:
        import pytest

        from aio.agents.prompts import load_agent_template

        with pytest.raises(ValueError):
            load_agent_template("nonexistent-agent", "outline")

    def test_unknown_command_raises_value_error(self) -> None:
        import pytest

        from aio.agents.prompts import load_agent_template

        with pytest.raises(ValueError):
            load_agent_template("claude", "nonexistent-command")

    def test_no_network_call_made(self, monkeypatch) -> None:
        # Verify load_agent_template doesn't open a socket
        original_connect = socket.socket.connect

        connections: list[tuple] = []

        def mock_connect(self, address):
            connections.append(address)
            return original_connect(self, address)

        monkeypatch.setattr(socket.socket, "connect", mock_connect)

        from aio.agents.prompts import load_agent_template

        load_agent_template("claude", "outline")
        assert len(connections) == 0, f"Network connection made: {connections}"

    def test_outputs_differ_between_agents(self) -> None:
        from aio.agents.prompts import load_agent_template

        agents = ["claude", "gemini", "chatgpt", "generic"]
        contents = {agent: load_agent_template(agent, "outline").content for agent in agents}
        # At least some agents should produce different output
        unique_contents = set(contents.values())
        assert len(unique_contents) > 1, "All agents produce identical output — format converters not working"
