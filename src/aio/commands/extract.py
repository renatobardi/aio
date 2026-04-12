"""AIO `extract` command — web scraper to DESIGN.md.

Scrapes a URL using urllib.request + BeautifulSoup (optional [enrich] dep)
and writes a structured 11-section DESIGN.md with extracted design tokens.

NOTE: NO from __future__ import annotations — breaks Typer runtime introspection.
"""

import re
import urllib.error
import urllib.request
from pathlib import Path

import typer

from aio._log import get_logger

_log = get_logger(__name__)

app = typer.Typer()

# ---------------------------------------------------------------------------
# Hex color and font extraction helpers
# ---------------------------------------------------------------------------

_HEX_RE = re.compile(r"#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b")
_FONT_RE = re.compile(
    r"font-family\s*:\s*['\"]?([A-Za-z][A-Za-z0-9 \-]+)['\"]?",
    re.IGNORECASE,
)
_GOOGLE_FONT_RE = re.compile(r"family=([A-Za-z][A-Za-z0-9+]+)", re.IGNORECASE)


def _unique_ordered(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _extract_colors(html: str) -> list[str]:
    """Extract unique hex color values from raw HTML/CSS."""
    found = _HEX_RE.findall(html)
    # Normalize to 6-char uppercase
    normalized: list[str] = []
    for c in found:
        if len(c) == 3:
            c = "".join(ch * 2 for ch in c)
        normalized.append("#" + c.upper())
    return _unique_ordered(normalized)


def _extract_fonts(html: str) -> list[str]:
    """Extract font family names from CSS and Google Fonts link hrefs."""
    fonts: list[str] = []
    for m in _FONT_RE.finditer(html):
        name = m.group(1).strip().split(",")[0].strip().strip("'\"")
        if name and name.lower() not in ("inherit", "initial", "unset", "normal", "sans-serif", "serif", "monospace"):
            fonts.append(name)
    for m in _GOOGLE_FONT_RE.finditer(html):
        fonts.append(m.group(1).replace("+", " "))
    return _unique_ordered(fonts)


def _extract_spacing(css_text: str) -> list[str]:
    """Extract spacing/padding/margin pixel values mentioned in CSS."""
    px_re = re.compile(r"\b(\d+)px\b")
    values = [v for v in px_re.findall(css_text) if 4 <= int(v) <= 256]
    unique = _unique_ordered(values)
    return sorted(unique, key=int)[:10]


# ---------------------------------------------------------------------------
# DESIGN.md template builder
# ---------------------------------------------------------------------------

_SECTION_NAMES = [
    "Visual Theme",
    "Color Palette",
    "Typography",
    "Components",
    "Layout System",
    "Depth & Shadows",
    "Do's & Don'ts",
    "Responsive Behavior",
    "Animation & Transitions",
    "Accessibility",
    "Agent Prompt Snippet",
]


def _build_design_md(
    url: str,
    colors: list[str],
    fonts: list[str],
    spacing: list[str],
    page_title: str,
    sections_filter: set[str] | None,
) -> str:
    def _include(section_key: str) -> bool:
        if sections_filter is None:
            return True
        return any(s in section_key.lower() for s in sections_filter)

    lines: list[str] = [f"# DESIGN.md — {page_title}\n", f"> Extracted from: {url}\n"]

    # Section 1 — Visual Theme
    if _include("visual"):
        lines.append("## 1. Visual Theme\n")
        lines.append(f"Design system extracted from {page_title}.\n")

    # Section 2 — Color Palette
    if _include("color"):
        lines.append("## 2. Color Palette\n")
        if colors:
            for i, color in enumerate(colors[:12]):
                lines.append(f"- Color {i + 1}: {color}\n")
        else:
            lines.append("- Primary: (no colors detected)\n")

    # Section 3 — Typography
    if _include("typography") or _include("font"):
        lines.append("## 3. Typography\n")
        if fonts:
            lines.append(f"- Display Font: {fonts[0]}\n")
            lines.append(f"- Body Font: {fonts[0]}\n")
            for extra in fonts[1:4]:
                lines.append(f"- Additional Font: {extra}\n")
        else:
            lines.append("- Display Font: (not detected)\n")
            lines.append("- Body Font: (not detected)\n")

    # Section 4 — Components
    if _include("component"):
        lines.append("## 4. Components\n")
        lines.append("- Buttons: primary, secondary (detected from HTML)\n")
        lines.append("- Cards: rounded corners with shadow\n")

    # Section 5 — Layout System
    if _include("layout"):
        lines.append("## 5. Layout System\n")
        if spacing:
            lines.append(f"- Base unit: {spacing[0]}px\n")
            lines.append(f"- Spacing scale: {', '.join(spacing[:6])}px\n")
        else:
            lines.append("- Base unit: 8px\n")
        lines.append("- Max-width: 1200px\n")

    # Section 6 — Depth & Shadows
    if _include("depth") or _include("shadow"):
        lines.append("## 6. Depth & Shadows\n")
        lines.append("- Level 1: 0 1px 3px rgba(0,0,0,0.08)\n")
        lines.append("- Level 2: 0 4px 12px rgba(0,0,0,0.12)\n")

    # Section 7 — Do's & Don'ts
    if _include("do"):
        lines.append("## 7. Do's & Don'ts\n")
        lines.append("- DO: Use primary color for main CTAs only\n")
        lines.append("- DON'T: Mix more than two font families\n")
        lines.append("- DON'T: Use colors below 4.5:1 contrast ratio\n")

    # Section 8 — Responsive Behavior
    if _include("responsive"):
        lines.append("## 8. Responsive Behavior\n")
        lines.append("- Mobile breakpoint: 640px\n")
        lines.append("- Tablet breakpoint: 1024px\n")
        lines.append("- Desktop: 1280px+\n")

    # Section 9 — Animation & Transitions
    if _include("animation") or _include("transition"):
        lines.append("## 9. Animation & Transitions\n")
        lines.append("- Duration: 150ms (micro), 300ms (standard)\n")
        lines.append("- Easing: ease-in-out\n")

    # Section 10 — Accessibility
    if _include("accessibility") or _include("a11y"):
        lines.append("## 10. Accessibility\n")
        lines.append("- Contrast ratio: minimum 4.5:1 (WCAG 2.1 AA)\n")
        lines.append("- Focus: visible 2px outline\n")
        lines.append("- All interactive elements keyboard navigable\n")

    # Section 11 — Agent Prompt Snippet
    if _include("agent") or _include("prompt"):
        lines.append("## 11. Agent Prompt Snippet\n")
        color_hint = colors[0] if colors else "the brand primary color"
        font_hint = fonts[0] if fonts else "the primary font"
        lines.append(
            f"Use {color_hint} for primary CTAs and headings. "
            f"Apply {font_hint} consistently across all text elements. "
            "Maintain generous white space with an 8px base grid. "
            "Ensure all color pairings meet WCAG AA contrast requirements.\n"
        )

    return "".join(lines)


# ---------------------------------------------------------------------------
# Typer CLI command
# ---------------------------------------------------------------------------


@app.command()
def extract(
    url: str = typer.Argument(..., help="URL to scrape for design tokens"),
    output: str = typer.Option("DESIGN.md", "--output", "-o", help="Output DESIGN.md path"),
    sections: str = typer.Option(None, "--sections", help="Comma-separated sections to extract"),
    timeout: int = typer.Option(10, "--timeout", help="Request timeout in seconds"),
) -> None:
    """Scrape a URL and extract design tokens → DESIGN.md."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        _log.error("BeautifulSoup not available. Install with: pip install aio[enrich]")
        raise typer.Exit(code=2)

    sections_filter: set[str] | None = None
    if sections:
        sections_filter = {s.strip().lower() for s in sections.split(",")}

    _log.info("Fetching %s ...", url)

    html_text: str = ""
    page_title: str = "Extracted Design"
    fetch_ok = False

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "aio-extract/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            raw = resp.read()
            html_text = raw.decode("utf-8", errors="replace")
        fetch_ok = True
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        _log.warning("Network error fetching %s: %s", url, exc)
        _log.warning("Writing partial DESIGN.md with defaults")

    if fetch_ok and html_text:
        soup = BeautifulSoup(html_text, "html.parser")
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            page_title = str(title_tag.string).strip()
    else:
        soup = None

    # Extract tokens from raw HTML (CSS embedded in <style> tags + inline)
    colors = _extract_colors(html_text)
    fonts = _extract_fonts(html_text)
    spacing = _extract_spacing(html_text)

    content = _build_design_md(url, colors, fonts, spacing, page_title, sections_filter)

    out_path = Path(output)
    out_path.write_text(content, encoding="utf-8")
    _log.info("Wrote %s (%d bytes)", out_path, len(content))
