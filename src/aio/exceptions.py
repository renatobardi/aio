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


class ExternalURLError(AIOError):
    """External URL detected in build output (Art. II violation)."""

    def __init__(self, urls: list[str]) -> None:
        super().__init__(f"External URLs found in output: {urls}. All assets must be inlined.")
        self.urls = urls


class LayoutDefinitionError(AIOError):
    """Layout template file cannot be read or is structurally invalid."""


class LayoutRegistryError(AIOError):
    """Layout registry discovery failed (zero .j2 files or no fallback template)."""


class RenderValidationError(AIOError):
    """HTML fragment failed post-render safety checks (e.g. contains <script>)."""


class SlideContextError(AIOError):
    """SlideRenderContext is missing a required field for the chosen layout."""

    def __init__(self, layout_id: str, field: str) -> None:
        super().__init__(f"Layout '{layout_id}' requires field '{field}' but it is None.")
        self.layout_id = layout_id
        self.field = field


class DesignSectionParseError(AIOError):
    """DESIGN.md could not be parsed into the required 11 sections."""

    def __init__(self, message: str, missing: list[int] | None = None) -> None:
        super().__init__(message)
        self.missing = missing or []


class DesignSectionValidationError(AIOError):
    """A parsed DesignSection failed content validation rules."""


class ThemeValidationError(AIOError):
    """ThemeRecord deserialization failed due to missing or invalid fields."""

    def __init__(self, theme_id: str, errors: list[str]) -> None:
        super().__init__(f"Theme '{theme_id}' validation failed: {'; '.join(errors)}")
        self.theme_id = theme_id
        self.errors = errors


class BuildResultError(AIOError):
    """BuildResult construction failed (e.g. output file not written)."""
