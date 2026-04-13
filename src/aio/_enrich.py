"""Image enrichment engine for AIO — Pollinations.ai free API (Art. II: zero external URLs).

Implements:
  - EnrichContext dataclass
  - infer_prompt(title, body) → str
  - derive_seed(deck_title, slide_index) → int
  - _is_valid_jpeg(data) → bool
  - make_placeholder_svg() → str
  - EnrichEngine.enrich_all(contexts) → list[EnrichContext]
"""

from __future__ import annotations

import hashlib
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from aio._log import get_logger

_log = get_logger(__name__)

_POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"
_TAG_RE = re.compile(r"<[^>]+>")

# FR-368: theme-to-style hint mapping for Pollinations
_THEME_STYLE_HINTS: dict[str, str] = {
    "minimal": "minimalist clean white background professional",
    "modern": "modern bold vibrant tech startup",
    "vibrant": "colorful vibrant energetic creative",
    "stripe": "fintech professional clean blue",
    "linear": "dark minimal developer tool",
}


def infer_style_hint(theme_id: str) -> str:
    """Return a style hint string for Pollinations based on theme."""
    return _THEME_STYLE_HINTS.get(theme_id, "professional presentation slide")


@dataclass
class EnrichContext:
    """Per-slide enrichment state — prompt, seed, result bytes, and placeholder flag."""

    slide_index: int
    prompt: str
    seed: int
    image_bytes: bytes | None
    is_placeholder: bool
    error_message: str | None = None


def infer_prompt(title: str | None, body: str) -> str:
    """Infer an image generation prompt from slide title and body text.

    Strips HTML tags, concatenates title + first 80 chars of body, truncates to
    100 chars. Falls back to "Abstract presentation slide" if result < 3 chars.
    """
    clean_body = _TAG_RE.sub("", body).strip()
    parts = []
    if title and title.strip():
        parts.append(title.strip())
    if clean_body:
        parts.append(clean_body[:80])
    combined = " ".join(parts).strip()
    truncated = combined[:100].strip()
    if len(truncated) < 3:
        return "Abstract presentation slide"
    return truncated


def derive_seed(deck_title: str, slide_index: int) -> int:
    """Derive a deterministic int seed from deck title and slide index via sha256."""
    raw = f"{deck_title}:{slide_index}".encode()
    digest = hashlib.sha256(raw).hexdigest()
    return int(digest[:8], 16)


def _is_valid_jpeg(data: bytes) -> bool:
    """Return True if data starts with JPEG magic bytes (0xFF 0xD8 0xFF)."""
    return len(data) >= 3 and data[:3] == b"\xff\xd8\xff"


_PLACEHOLDER_SVG = (
    '<svg width="200" height="120">'
    '<rect width="200" height="120" fill="#e5e7eb"/>'
    '<text x="100" y="65" text-anchor="middle" font-size="12" fill="#6b7280">N/A</text>'
    "</svg>"
)


def make_placeholder_svg() -> str:
    """Return a minimal SVG grey rectangle with 'N/A' text (<200 bytes)."""
    return _PLACEHOLDER_SVG


class EnrichEngine:
    """Calls Pollinations.ai for each EnrichContext, validates JPEG, base64-encodes result."""

    def __init__(self, timeout: int = 30, style_hint: str = "") -> None:
        self._timeout = timeout
        self._style_hint = style_hint

    def enrich_all(self, contexts: list[EnrichContext]) -> list[EnrichContext]:
        """Enrich all contexts in-place; return updated list.

        For each context:
        - Builds Pollinations URL with prompt + seed
        - Fetches image with configured timeout
        - Validates JPEG magic bytes
        - Base64-encodes result
        - On any error: sets is_placeholder=True, logs warning
        """
        results: list[EnrichContext] = []
        for ctx in contexts:
            results.append(self._enrich_one(ctx))
        return results

    def _enrich_one(self, ctx: EnrichContext, style_hint: str = "") -> EnrichContext:
        effective_hint = style_hint or self._style_hint
        full_prompt = f"{ctx.prompt}, {effective_hint}" if effective_hint else ctx.prompt
        encoded_prompt = urllib.parse.quote(full_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={ctx.seed}&width=512&height=384&nologo=true"
        try:
            with urllib.request.urlopen(url, timeout=self._timeout) as resp:
                data = resp.read()
            if not _is_valid_jpeg(data):
                _log.warning(
                    "Slide %d: Pollinations response is not a valid JPEG — using placeholder",
                    ctx.slide_index,
                )
                return EnrichContext(
                    slide_index=ctx.slide_index,
                    prompt=ctx.prompt,
                    seed=ctx.seed,
                    image_bytes=None,
                    is_placeholder=True,
                    error_message="Invalid JPEG response",
                )
            return EnrichContext(
                slide_index=ctx.slide_index,
                prompt=ctx.prompt,
                seed=ctx.seed,
                image_bytes=data,
                is_placeholder=False,
            )
        except urllib.error.URLError as exc:
            _log.warning(
                "Slide %d: Failed to enrich via Pollinations (%s) — using placeholder",
                ctx.slide_index,
                exc,
            )
            return EnrichContext(
                slide_index=ctx.slide_index,
                prompt=ctx.prompt,
                seed=ctx.seed,
                image_bytes=None,
                is_placeholder=True,
                error_message=str(exc),
            )
        except Exception as exc:
            _log.warning("Slide %d: Unexpected enrich error: %s — using placeholder", ctx.slide_index, exc)
            return EnrichContext(
                slide_index=ctx.slide_index,
                prompt=ctx.prompt,
                seed=ctx.seed,
                image_bytes=None,
                is_placeholder=True,
                error_message=str(exc),
            )
