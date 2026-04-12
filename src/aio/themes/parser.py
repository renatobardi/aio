"""
DESIGN.md parser for AIO themes (Art. V — 11 sections mandatory).

Implements:
  - DesignSection dataclass
  - parse_design_md(text) -> list[DesignSection]
  - extract_css_vars(sections) -> str  (generates :root { --color-*; --font-*; })
  - extract_layout_css(sections) -> str (generates .layout-* CSS class stubs)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml

from aio._log import get_logger
from aio.exceptions import DesignSectionParseError, DesignSectionValidationError

_log = get_logger(__name__)

# Matches "## N. Heading" or "## N Heading" at the start of a line
# Anchored at ^ and $ — .+ (greedy) cannot backtrack past the end-of-line anchor
SECTION_RE = re.compile(
    r"^##\s+(\d+)\.?\s+(.+)$",
    re.MULTILINE,
)

# [^\n]* matches optional trailing chars on the ```yaml line; avoids \s*\n backtracking
YAML_FENCE_RE = re.compile(r"```yaml[^\n]*\n(.*?)```", re.DOTALL)

# Color hex extraction from plain text lines (e.g. "- Primary: #635BFF")
COLOR_LINE_RE = re.compile(r"([A-Za-z][\w\s-]*?):\s*(#[0-9a-fA-F]{3,6})\b")

# Font name extraction (e.g. "Display Font: Inter")
FONT_LINE_RE = re.compile(r"(?:display|heading|body|mono)\s+font[:\s]+([A-Za-z][\w\s]+)", re.IGNORECASE)

REQUIRED_SECTIONS = 11
MIN_CHAR_COUNT = 50
MIN_AGENT_PROMPT_CHARS = 200


@dataclass
class DecorationSpec:
    """One CSS decoration rule extracted from DESIGN.md section 12."""

    name: str
    css_class: str
    css_value: str
    css_property: str
    responsive_value: str | None = None


@dataclass
class DesignSection:
    """One parsed section from a DESIGN.md file."""

    section_number: int
    heading: str
    raw_content: str
    parsed_data: dict[str, object] = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        return len(self.raw_content)


def parse_design_md(text: str) -> list[DesignSection]:
    """
    Parse a DESIGN.md string into exactly 11 DesignSection objects.

    Raises DesignSectionParseError if fewer than 11 sections found or
    if section numbers are non-contiguous.
    Raises DesignSectionValidationError for section-level content violations.
    """
    matches = list(SECTION_RE.finditer(text))

    if len(matches) < REQUIRED_SECTIONS:
        found_numbers = [int(m.group(1)) for m in matches]
        missing = [i for i in range(1, REQUIRED_SECTIONS + 1) if i not in found_numbers]
        raise DesignSectionParseError(
            f"DESIGN.md has only {len(matches)} sections; expected {REQUIRED_SECTIONS}. Missing: {missing}",
            missing=missing,
        )

    sections: list[DesignSection] = []
    for i, match in enumerate(matches):
        number = int(match.group(1))
        heading = match.group(2).strip()

        # Content is everything from after this heading to the next heading (or end)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        raw_content = text[start:end].strip()

        # Parse fenced YAML blocks
        parsed_data: dict[str, object] = {}
        yaml_match = YAML_FENCE_RE.search(raw_content)
        if yaml_match:
            try:
                result = yaml.safe_load(yaml_match.group(1))
                if isinstance(result, dict):
                    parsed_data = result
            except yaml.YAMLError as exc:
                _log.warning("Section %d YAML parse error: %s", number, exc)
                parsed_data = {"_parse_error": str(exc)}

        sections.append(
            DesignSection(
                section_number=number,
                heading=heading,
                raw_content=raw_content,
                parsed_data=parsed_data,
            )
        )

    # Validate non-contiguous section numbers
    numbers = [s.section_number for s in sections[:REQUIRED_SECTIONS]]
    if numbers != list(range(1, REQUIRED_SECTIONS + 1)):
        raise DesignSectionParseError(f"Section numbers are non-contiguous: {numbers}")

    # Validate minimum content per section (sections 1–10)
    for s in sections[:10]:
        if s.char_count < MIN_CHAR_COUNT:
            _log.warning(
                "Section %d ('%s') has only %d chars (minimum %d)",
                s.section_number,
                s.heading,
                s.char_count,
                MIN_CHAR_COUNT,
            )

    # Validate section 2 — Color Palette must have at least one hex value
    color_section = sections[1]  # section_number == 2
    has_hex = bool(re.search(r"#[0-9a-fA-F]{3,6}", color_section.raw_content))
    if not has_hex and not color_section.parsed_data:
        raise DesignSectionValidationError("Section 2 (Color Palette) must contain at least one hex color value.")

    # Validate section 11 — Agent Prompt Snippet must be >= 200 chars
    agent_section = sections[10]  # section_number == 11
    if agent_section.char_count < MIN_AGENT_PROMPT_CHARS:
        raise DesignSectionValidationError(
            f"Section 11 (Agent Prompt Snippet) has {agent_section.char_count} chars; "
            f"minimum is {MIN_AGENT_PROMPT_CHARS}."
        )

    # Include optional section 12 (Decorations) if present
    if len(sections) > REQUIRED_SECTIONS and sections[REQUIRED_SECTIONS].section_number == 12:
        section12 = sections[REQUIRED_SECTIONS]
        decorations = _parse_decoration_section(section12.raw_content)
        section12.parsed_data["decorations"] = decorations
        return sections[:REQUIRED_SECTIONS] + [section12]

    return sections[:REQUIRED_SECTIONS]


# Regex for "- name: value" decoration lines inside section 12
_DECORATION_LINE_RE = re.compile(r"^\s*-\s+([\w-]+)\s*:\s*(.+)$", re.MULTILINE)

# Map decoration category keywords → CSS property
_DECORATION_CSS_PROPERTY: dict[str, str] = {
    "gradient": "background",
    "glow": "box-shadow",
    "divider": "border",
    "accent": "border-left",
}

# Default fallback decoration classes when section 12 is absent
_DEFAULT_DECORATION_CSS = (
    ".decoration-gradient-primary {"
    " background: linear-gradient(135deg, var(--color-primary, #635BFF) 0%, var(--color-accent, #00D084) 100%);"
    " }\n"
    ".decoration-glow-primary { box-shadow: 0 0 30px rgba(99, 91, 255, 0.4); }\n"
    ".decoration-divider-thin { border-top: 1px solid var(--color-neutral-300, #d1d5db); }\n"
    ".decoration-accent-left { border-left: 4px solid var(--color-primary, #635BFF); padding-left: 1rem; }\n"
)


def _parse_decoration_section(raw_content: str) -> list[DecorationSpec]:
    """Parse the raw content of DESIGN.md section 12 into DecorationSpec objects."""
    specs: list[DecorationSpec] = []
    current_category = "general"

    for line in raw_content.splitlines():
        # Track sub-heading to infer CSS property
        stripped = line.strip()
        if stripped.startswith("###"):
            current_category = stripped.lstrip("#").strip().lower()
            continue

        m = _DECORATION_LINE_RE.match(line)
        if not m:
            continue

        name = m.group(1).strip()
        value = m.group(2).strip()

        # Infer CSS property from category heading
        css_property = "background"
        for keyword, prop in _DECORATION_CSS_PROPERTY.items():
            if keyword in current_category:
                css_property = prop
                break

        # Build CSS class name: decoration-{category_keyword}-{name}
        category_slug = next(
            (k for k in _DECORATION_CSS_PROPERTY if k in current_category),
            current_category.split()[0] if current_category.split() else "decoration",
        )
        css_class = f"decoration-{category_slug}-{name}"

        specs.append(DecorationSpec(
            name=name,
            css_class=css_class,
            css_value=value,
            css_property=css_property,
        ))

    return specs


def generate_decoration_css(specs: list[DecorationSpec], *, enabled: bool = True) -> str:
    """Emit `.decoration-{name} { {property}: {value}; }` CSS from DecorationSpec list.

    If ``specs`` is empty, emits four default fallback classes.
    If ``enabled`` is False, returns empty string (decorations disabled).
    """
    if not enabled:
        return ""
    if not specs:
        return _DEFAULT_DECORATION_CSS
    lines: list[str] = []
    for spec in specs:
        lines.append(f".{spec.css_class} {{ {spec.css_property}: {spec.css_value}; }}")
    return "\n".join(lines) + "\n"


def extract_css_vars(sections: list[DesignSection]) -> str:
    """
    Generate :root { --color-*: hex; --font-*: name; } CSS from sections 2 and 3.

    Section 2 — Color Palette → --color-{name}: #hex;
    Section 3 — Typography → --font-display / --font-body / --font-mono
    """
    lines: list[str] = []

    # Section 2: Color Palette
    color_section = next((s for s in sections if s.section_number == 2), None)
    if color_section:
        # From parsed_data (fenced YAML block)
        for key, val in color_section.parsed_data.items():
            if key.startswith("_"):
                continue
            if isinstance(val, str) and re.match(r"^#[0-9a-fA-F]{3,6}$", val.strip()):
                css_name = re.sub(r"[^a-z0-9]", "-", key.lower()).strip("-")
                lines.append(f"  --color-{css_name}: {val.strip()};")

        # From plain text lines (fallback)
        if not lines:
            for match in COLOR_LINE_RE.finditer(color_section.raw_content):
                name = re.sub(r"[^a-z0-9]", "-", match.group(1).lower()).strip("-")
                hex_val = match.group(2)
                lines.append(f"  --color-{name}: {hex_val};")

    # Section 3: Typography
    typo_section = next((s for s in sections if s.section_number == 3), None)
    if typo_section:
        data = typo_section.parsed_data
        if "heading_font" in data:
            lines.append(f"  --font-display: '{data['heading_font']}', sans-serif;")
        if "body_font" in data:
            lines.append(f"  --font-body: '{data['body_font']}', sans-serif;")
        if "mono_font" in data:
            lines.append(f"  --font-mono: '{data['mono_font']}', monospace;")

        # Fallback: plain text font lines
        if not any("--font-" in ln for ln in lines):
            for match in FONT_LINE_RE.finditer(typo_section.raw_content):
                font_name = match.group(1).strip().rstrip(".")
                keyword = match.group(0).lower()
                if "display" in keyword or "heading" in keyword:
                    lines.append(f"  --font-display: '{font_name}', sans-serif;")
                elif "body" in keyword:
                    lines.append(f"  --font-body: '{font_name}', sans-serif;")
                elif "mono" in keyword:
                    lines.append(f"  --font-mono: '{font_name}', monospace;")

    if not lines:
        return ""

    return ":root {\n" + "\n".join(lines) + "\n}\n"


def extract_layout_css(sections: list[DesignSection]) -> str:
    """
    Generate .layout-* CSS class stubs from sections 4 (Components) and 5 (Layout System).

    Produces skeleton rules mapping semantic layout names to CSS var references.
    Used by the import script and theme create scaffold.
    """
    known_layouts = [
        "hero-title",
        "stat-highlight",
        "split-image-text",
        "content-with-icons",
        "comparison-2col",
        "quote",
        "key-takeaways",
        "closing",
        "content",
    ]

    # Gather any color/font hints from sections 2–3
    color_primary = "--color-primary"
    color_accent = "--color-accent"
    font_display = "--font-display"
    font_body = "--font-body"

    color_section = next((s for s in sections if s.section_number == 2), None)
    if color_section:
        data = color_section.parsed_data
        if "primary" in data:
            color_primary = "--color-primary"
        if "accent" in data:
            color_accent = "--color-accent"

    blocks: list[str] = []

    for layout_id in known_layouts:
        css_class = f".layout-{layout_id}"
        if layout_id == "hero-title":
            blocks.append(
                f"{css_class} h1.hero-title {{\n  color: var({color_primary});\n  font-family: var({font_display});\n}}"
            )
        elif layout_id == "stat-highlight":
            blocks.append(
                f"{css_class} .stat {{\n"
                f"  color: var({color_accent});\n"
                f"  font-family: var({font_display});\n"
                f"  font-size: 5rem;\n"
                f"}}"
            )
        elif layout_id == "quote":
            blocks.append(
                f"{css_class} blockquote {{\n"
                f"  font-family: var({font_display});\n"
                f"  border-left: 4px solid var({color_primary});\n"
                f"}}"
            )
        else:
            blocks.append(f"{css_class} {{\n  font-family: var({font_body});\n}}")

    return "\n\n".join(blocks) + "\n"
