"""
Core dataclasses for the AIO build pipeline.

SlideRenderContext  — context dict passed to Jinja2 layout templates (COMPOSE step).
ComposedSlide       — output of the COMPOSE step for a single slide.
BuildResult         — returned by the build command after the full pipeline.
HotReloadEvent      — internal event passed via asyncio.Queue in serve hot-reload.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class SlideRenderContext:
    """Complete context passed to jinja2 layout template rendering."""

    # Slide identity
    slide_index: int
    slide_id: str

    # Layout selection
    layout_id: str
    is_inferred: bool = True

    # Core content (pre-rendered HTML strings from mistune)
    title: str | None = None
    body_html: str = ""
    speaker_notes: str | None = None

    # Per-layout structured fields
    stat_value: str | None = None
    stat_label: str | None = None
    stat_description: str | None = None
    quote_text: str | None = None
    quote_attribution: str | None = None
    image_src: str | None = None  # base64 data URI
    image_alt: str | None = None
    image_position: str = "right"  # "left" or "right"
    cta_text: str | None = None

    # Comparison layout
    left_title: str | None = None
    left_content: str | None = None
    right_title: str | None = None
    right_content: str | None = None

    # Theme CSS custom properties to inject
    theme_vars: dict[str, str] = field(default_factory=dict)

    # Reveal.js data attributes
    reveal_attrs: dict[str, str] = field(default_factory=dict)

    # Metadata
    tags: list[str] = field(default_factory=list)
    duration_hint: int | None = None

    def __post_init__(self) -> None:
        if self.slide_index < 0:
            raise ValueError(f"slide_index must be >= 0, got {self.slide_index}")
        if not self.slide_id:
            object.__setattr__(self, "slide_id", f"slide-{self.slide_index}")
        if self.image_position not in ("left", "right"):
            raise ValueError(f"image_position must be 'left' or 'right', got '{self.image_position}'")
        if self.duration_hint is not None and self.duration_hint <= 0:
            raise ValueError(f"duration_hint must be > 0, got {self.duration_hint}")


@dataclass
class ComposedSlide:
    """Output of the COMPOSE step for a single slide."""

    index: int
    layout_id: str
    html_fragment: str
    render_context: SlideRenderContext
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError(f"index must be >= 0, got {self.index}")
        stripped = self.html_fragment.strip()
        if not stripped.startswith("<section") or not stripped.endswith("</section>"):
            raise ValueError("html_fragment must start with <section and end with </section>")
        if "<script" in self.html_fragment.lower():
            raise ValueError("html_fragment must not contain <script tags (constitution rule 7)")


@dataclass
class BuildResult:
    """Returned by the build command after the full pipeline completes."""

    output_path: Path
    slide_count: int
    byte_size: int
    theme_id: str
    elapsed_seconds: float
    layout_histogram: dict[str, int] = field(default_factory=dict)
    warning_count: int = 0
    enrich_used: bool = False

    def __post_init__(self) -> None:
        if self.slide_count < 1:
            raise ValueError(f"slide_count must be >= 1, got {self.slide_count}")
        if self.byte_size < 1:
            raise ValueError(f"byte_size must be >= 1, got {self.byte_size}")
        if self.elapsed_seconds < 0.0:
            raise ValueError(f"elapsed_seconds must be >= 0.0, got {self.elapsed_seconds}")

    def to_dict(self) -> dict[str, object]:
        d = dataclasses.asdict(self)
        d["output_path"] = str(self.output_path)
        return d


@dataclass(frozen=True)
class HotReloadEvent:
    """Internal event passed via asyncio.Queue from watchdog to SSE handler."""

    event_type: Literal["reload", "error"]
    message: str
    source_path: Path | None = None
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.event_type not in ("reload", "error"):
            raise ValueError(f"event_type must be 'reload' or 'error', got '{self.event_type}'")
        if not self.message:
            raise ValueError("message must be non-empty")
        if len(self.message) > 500:
            object.__setattr__(self, "message", self.message[:500])
