"""AIO exception hierarchy."""
from __future__ import annotations


class AIOError(Exception):
    """Base exception for all AIO errors."""

    def __init__(self, message: str, suggestion: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion


class ConfigError(AIOError):
    """ProjectConfig load/validation failures."""


class LayoutNotFoundError(AIOError):
    """Unknown layout name; includes fuzzy suggestion when available."""

    def __init__(self, name: str, suggestion: str | None = None) -> None:
        msg = f"Layout '{name}' not found in registry."
        if suggestion:
            msg += f" Did you mean '{suggestion}'?"
        super().__init__(msg, suggestion)
        self.name = name


class ThemeNotFoundError(AIOError):
    """Unknown theme ID."""

    def __init__(self, theme_id: str) -> None:
        super().__init__(f"Theme '{theme_id}' not found in registry.")
        self.theme_id = theme_id


class ParseError(AIOError):
    """slides.md parsing failure."""

    def __init__(self, message: str, line: int | None = None) -> None:
        full_msg = f"Parse error{f' at line {line}' if line else ''}: {message}"
        super().__init__(full_msg)
        self.line = line


class AgentError(AIOError):
    """Agent template loading failure."""
