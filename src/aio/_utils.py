"""Utility functions for AIO."""

from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path

import jinja2

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


def escape_script(text: str) -> str:
    """
    Escape </script> inside inline JS to prevent premature tag closure (Art. VIII).
    Replaces </script with <\\/script.
    """
    return text.replace("</script", r"<\/script")


def build_jinja_env(templates_package: str = "aio.layouts") -> jinja2.Environment:
    """
    Build a Jinja2 Environment using importlib.resources loader.
    Registers the escape_script custom filter.
    Works in all 4 distribution modes (Art. XII).
    """
    import importlib.resources

    pkg = importlib.resources.files(templates_package)
    loader = jinja2.FunctionLoader(
        lambda name: (pkg / name).read_text(encoding="utf-8")
    )
    env = jinja2.Environment(
        loader=loader,
        autoescape=False,  # HTML fragments are pre-sanitised upstream  # NOSONAR
        undefined=jinja2.Undefined,
    )
    env.filters["escape_script"] = escape_script
    return env


def base64_inline(image_path: Path) -> str:
    """
    Read an image file and return a base64 data URI string.

    SVG files are returned as raw inline XML (data:image/svg+xml;charset=utf-8,...).
    All other formats are base64-encoded (data:image/png;base64,...).
    Raises FileNotFoundError if the path does not exist.
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    mime, _ = mimetypes.guess_type(str(image_path))
    mime = mime or "application/octet-stream"

    raw = image_path.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


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
