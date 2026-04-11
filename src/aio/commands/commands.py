"""AIO `commands` subcommand group — agent prompt templates."""
# NOTE: NO `from __future__ import annotations` in this file.
# Typer relies on runtime type introspection; postponed evaluation breaks it.

import typer

from aio._log import get_logger

_log = get_logger(__name__)

app = typer.Typer(
    name="commands",
    help="Agent command templates (outline, generate, refine, visual, theme, extract, build)",
)


@app.command("list")
def list_commands() -> None:
    """List all available agent commands."""
    try:
        from aio.agents.prompts import list_commands as _list_commands

        commands = _list_commands()
        for name, description in commands:
            typer.echo(f"{name:12} — {description}")
    except Exception as exc:
        _log.error("Failed to list commands: %s", exc)
        raise typer.Exit(code=1)
    _log.info("Command complete")


def _make_command(cmd_name: str) -> None:
    """Factory: create a Typer command for each agent command."""

    @app.command(cmd_name)
    def _cmd(
        agent: str = typer.Option("claude", "--agent", "-a", help="AI agent"),
        copy: bool = typer.Option(False, "--copy", "-c", help="Copy prompt to clipboard"),
    ) -> None:
        """Output the prompt for the given agent."""
        try:
            from aio.agents.prompts import load_agent_template

            tmpl = load_agent_template(agent, cmd_name)
            content = tmpl.content
        except Exception as exc:
            _log.error("%s", exc)
            raise typer.Exit(code=1)

        if copy:
            try:
                import pyperclip

                pyperclip.copy(content)
                _log.info("Prompt copied to clipboard.")
            except Exception:
                typer.echo(content)
        else:
            typer.echo(content)
        _log.info("Command complete")

    _cmd.__name__ = cmd_name


_COMMAND_NAMES = ["outline", "generate", "refine", "visual", "theme", "extract", "build"]
for _name in _COMMAND_NAMES:
    _make_command(_name)
