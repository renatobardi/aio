"""Agent command template loading — vendored, offline-only (Art. XI)."""
from __future__ import annotations

import importlib.resources
from collections.abc import Callable
from dataclasses import dataclass

from aio._log import get_logger

_log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Supported commands and agents
# ---------------------------------------------------------------------------

SUPPORTED_COMMANDS: dict[str, str] = {
    "outline": "Generate slide outline from topic",
    "generate": "Generate full slide deck with content",
    "refine": "Refine existing deck (tone, length, focus)",
    "visual": "Add visual descriptions and layout annotations",
    "theme": "Suggest theme and design system alignment",
    "extract": "Extract DESIGN.md from a website",
    "build": "Orchestrate all steps end-to-end",
}

SUPPORTED_AGENTS: frozenset[str] = frozenset(
    {"claude", "gemini", "copilot", "windsurf", "devin", "chatgpt", "cursor", "generic"}
)

# Agents that use a SYSTEM + USER prompt structure
_SYSTEM_PROMPT_AGENTS: frozenset[str] = frozenset({"claude", "copilot", "chatgpt"})


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class AgentCommandTemplate:
    """Rendered prompt template for a specific agent + command combination."""

    agent: str
    command: str
    version: str
    content: str
    has_system_prompt: bool


# ---------------------------------------------------------------------------
# Format converters (T075)
# ---------------------------------------------------------------------------


def _fmt_claude(system: str, user: str) -> str:
    return f"SYSTEM:\n{system}\n\nUSER:\n{user}"


def _fmt_copilot(system: str, user: str) -> str:
    return f"SYSTEM:\n{system}\n\nUSER:\n{user}"


def _fmt_chatgpt(system: str, user: str) -> str:
    return f"SYSTEM:\n{system}\n\nUSER:\n{user}"


def _fmt_user_only(_system: str, user: str) -> str:
    return user


FORMAT_CONVERTERS: dict[str, Callable[[str, str], str]] = {
    "claude": _fmt_claude,
    "copilot": _fmt_copilot,
    "chatgpt": _fmt_chatgpt,
    "gemini": _fmt_user_only,
    "windsurf": _fmt_user_only,
    "devin": _fmt_user_only,
    "cursor": _fmt_user_only,
    "generic": _fmt_user_only,
}


# ---------------------------------------------------------------------------
# Public API (T073, T074)
# ---------------------------------------------------------------------------


def list_commands() -> list[tuple[str, str]]:
    """Return list of (command_name, description) tuples for all 7 commands."""
    return list(SUPPORTED_COMMANDS.items())


def list_agents() -> list[str]:
    """Return list of all supported agent names."""
    return sorted(SUPPORTED_AGENTS)


def load_agent_template(
    agent: str,
    command: str,
    version: str = "v1",
) -> AgentCommandTemplate:
    """Load and format a command template for the given agent.

    Uses importlib.resources — works in all 4 distribution modes (Art. XII).
    No network calls; all templates are vendored.

    Raises:
        ValueError: if agent or command is not supported
        FileNotFoundError: if template file is missing
    """
    if agent not in SUPPORTED_AGENTS:
        raise ValueError(
            f"Unknown agent '{agent}'. Supported: {', '.join(sorted(SUPPORTED_AGENTS))}"
        )
    if command not in SUPPORTED_COMMANDS:
        raise ValueError(
            f"Unknown command '{command}'. Supported: {', '.join(SUPPORTED_COMMANDS.keys())}"
        )

    pkg_root = importlib.resources.files("aio.agent_commands")

    # Load system prompt for this agent (if it has one)
    system_content = ""
    has_system_prompt = agent in _SYSTEM_PROMPT_AGENTS
    if has_system_prompt:
        try:
            system_ref = pkg_root / agent / version / "SYSTEM.md"
            system_content = system_ref.read_text(encoding="utf-8")
        except Exception as exc:
            _log.warning("Could not load SYSTEM.md for %s/%s: %s", agent, version, exc)
            has_system_prompt = False

    # Load generic command template
    try:
        user_ref = pkg_root / f"{command}.md"
        user_content = user_ref.read_text(encoding="utf-8")
    except Exception as exc:
        raise FileNotFoundError(
            f"Template '{command}.md' not found in agent_commands/"
        ) from exc

    # Apply format converter
    converter = FORMAT_CONVERTERS.get(agent, _fmt_user_only)
    content = converter(system_content, user_content)

    _log.debug("Loaded template: agent=%s, command=%s, version=%s", agent, command, version)
    return AgentCommandTemplate(
        agent=agent,
        command=command,
        version=version,
        content=content,
        has_system_prompt=has_system_prompt,
    )
