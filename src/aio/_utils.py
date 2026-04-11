"""Utility functions for AIO."""

from __future__ import annotations

import re
from pathlib import Path

from aio.exceptions import AIOError


def slugify(text: str) -> str:
    """Convert text to lowercase hyphen-slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def safe_id(text: str) -> str:
    """Convert text to a CSS-safe identifier (no leading digit)."""
    slug = slugify(text)
    if slug and slug[0].isdigit():
        slug = "id-" + slug
    return slug or "id"


def escape_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def find_aio_dir(start: Path) -> Path:
    """
    Walk parent directories to find the nearest .aio/ directory.

    Raises AIOError if not found.
    """
    for parent in [start, *start.parents]:
        aio_dir = parent / ".aio"
        if aio_dir.is_dir():
            return aio_dir
    raise AIOError("No .aio/ directory found. Run 'aio init' first.")
