"""Validation utilities. All YAML parsing uses yaml.safe_load() exclusively."""

from __future__ import annotations

import re
from typing import Any

import yaml

from aio.exceptions import ParseError

# Matches external http(s):// URLs in src= or href= HTML attributes
_EXTERNAL_URL_RE = re.compile(
    r"""(?:src|href)\s*=\s*["'](https?://[^"']+)["']""",
    re.IGNORECASE,
)


def yaml_safe_load(content: str, source: str = "") -> dict[str, Any]:
    """
    Wrap yaml.safe_load with ParseError on failure.
    NEVER calls yaml.load() — safe_load only.
    """
    try:
        result = yaml.safe_load(content)
        return result if isinstance(result, dict) else {}
    except yaml.YAMLError as exc:
        line: int | None = None
        if hasattr(exc, "problem_mark") and exc.problem_mark is not None:
            line = exc.problem_mark.line + 1
        raise ParseError(
            f"Invalid YAML{f' in {source}' if source else ''}: {exc}",
            line=line,
        ) from exc


def validate_json_schema(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """
    Minimal JSON schema validation (required fields only).
    Returns a list of error strings (empty if valid).
    """
    errors: list[str] = []
    for field in schema.get("required", []):
        if field not in data:
            errors.append(f"Missing required field: '{field}'")
    return errors


def check_external_urls(html: str) -> list[str]:
    """
    Return a list of external https?:// URLs found in src= or href= attributes.

    An empty list means the HTML passes the external-URL check (Art. II compliance).
    """
    return _EXTERNAL_URL_RE.findall(html)
