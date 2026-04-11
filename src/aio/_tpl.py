"""Jinja2 environment factory. Uses PackageLoader for all dist modes (Art. XII)."""

from __future__ import annotations

import jinja2
import mistune

from aio._utils import safe_id, slugify


def _markdown_filter(value: str) -> str:
    """Render markdown string to HTML."""
    md = mistune.create_markdown()
    result = md(value)
    if isinstance(result, str):
        return result
    return ""


def _to_css_var(value: str) -> str:
    """Convert a string to a CSS custom property name (e.g. --my-var)."""
    return "--" + slugify(value)


def make_jinja_env() -> jinja2.Environment:
    """
    Create the shared Jinja2 Environment.

    Uses PackageLoader("aio", "layouts") — works in pip, zipapp, and
    PyInstaller modes (Art. XII). FileSystemLoader MUST NOT be used here.
    """
    env = jinja2.Environment(
        loader=jinja2.PackageLoader("aio", "layouts"),
        autoescape=False,
        keep_trailing_newline=True,
    )
    env.filters["markdown"] = _markdown_filter
    env.filters["safe_id"] = safe_id
    env.filters["to_css_var"] = _to_css_var
    # "truncate" is a Jinja2 built-in filter — no registration needed
    return env
