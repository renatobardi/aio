"""Structured stderr logging for AIO. Never writes to stdout."""
from __future__ import annotations

import logging
import os
import re
import sys

_API_KEY_RE = re.compile(r"[0-9a-f]{32,}", re.IGNORECASE)
_BEARER_RE = re.compile(r"Bearer\s+\S+", re.IGNORECASE)


def _mask_sensitive(msg: str) -> str:
    """Redact API key patterns and Bearer tokens from log messages."""
    msg = _API_KEY_RE.sub("***", msg)
    msg = _BEARER_RE.sub("Bearer ***", msg)
    return msg


class _MaskingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.msg = _mask_sensitive(str(record.msg))
        return super().format(record)


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root 'aio' logger to write structured messages to stderr.

    Idempotent: calling multiple times does not duplicate handlers.
    Respects AIO_LOG_LEVEL env var; explicit level argument takes precedence.
    """
    env_level_str = os.environ.get("AIO_LOG_LEVEL", "").upper()
    if env_level_str:
        env_level = getattr(logging, env_level_str, None)
        if isinstance(env_level, int) and level == logging.INFO:
            # Env var only overrides when caller didn't explicitly choose a level
            level = env_level

    root = logging.getLogger("aio")
    if root.handlers:
        root.setLevel(level)
        for handler in root.handlers:
            handler.setLevel(level)
        return

    root.setLevel(level)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    formatter = _MaskingFormatter("%(levelname)s [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a child logger of the 'aio' root logger."""
    return logging.getLogger(name)
