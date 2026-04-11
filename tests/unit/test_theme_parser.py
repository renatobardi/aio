"""Unit tests for themes/parser.py — parse_design_md, extract_css_vars, extract_layout_css (T025)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aio.exceptions import DesignSectionParseError, DesignSectionValidationError
from aio.themes.parser import (
    DesignSection,
    extract_css_vars,
    extract_layout_css,
    parse_design_md,
)

FIXTURE_DESIGN_MD = Path(__file__).parent.parent / "fixtures" / "themes" / "fixture_theme" / "DESIGN.md"


@pytest.fixture(scope="module")
def fixture_text() -> str:
    return FIXTURE_DESIGN_MD.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def fixture_sections(fixture_text: str) -> list[DesignSection]:
    return parse_design_md(fixture_text)


# ---------------------------------------------------------------------------
# parse_design_md — happy path
# ---------------------------------------------------------------------------


def test_returns_11_sections(fixture_sections: list[DesignSection]) -> None:
    assert len(fixture_sections) == 11


def test_section_numbers_contiguous(fixture_sections: list[DesignSection]) -> None:
    numbers = [s.section_number for s in fixture_sections]
    assert numbers == list(range(1, 12))


def test_section_headings_non_empty(fixture_sections: list[DesignSection]) -> None:
    for s in fixture_sections:
        assert s.heading.strip(), f"Section {s.section_number} heading is empty"


def test_section_2_parsed_data_has_colors(fixture_sections: list[DesignSection]) -> None:
    color_section = fixture_sections[1]  # section_number == 2
    assert color_section.section_number == 2
    assert color_section.parsed_data, "Section 2 parsed_data must not be empty"
    # YAML parsed from fenced block — must contain at least the 'primary' key
    assert "primary" in color_section.parsed_data


def test_section_2_raw_content_has_hex(fixture_sections: list[DesignSection]) -> None:
    import re

    color_section = fixture_sections[1]
    assert re.search(r"#[0-9a-fA-F]{3,6}", color_section.raw_content)


def test_section_3_parsed_data_has_fonts(fixture_sections: list[DesignSection]) -> None:
    typo = fixture_sections[2]  # section_number == 3
    assert typo.section_number == 3
    assert "heading_font" in typo.parsed_data or "body_font" in typo.parsed_data


def test_section_11_char_count_sufficient(fixture_sections: list[DesignSection]) -> None:
    agent_section = fixture_sections[10]  # section_number == 11
    assert agent_section.char_count >= 200, f"Section 11 has only {agent_section.char_count} chars; expected >= 200"


def test_char_count_property() -> None:
    s = DesignSection(section_number=1, heading="Test", raw_content="hello world")
    assert s.char_count == len("hello world")


# ---------------------------------------------------------------------------
# parse_design_md — error cases
# ---------------------------------------------------------------------------


def test_fewer_than_11_sections_raises() -> None:
    text = "\n".join(f"## {i}. Section {i}\n\nContent {i}." for i in range(1, 8))
    with pytest.raises(DesignSectionParseError) as exc_info:
        parse_design_md(text)
    err = exc_info.value
    assert err.missing  # missing list must be populated
    assert 8 in err.missing or len(err.missing) > 0


def test_missing_sections_listed_in_error() -> None:
    # Provide sections 1-10 but skip 11
    parts = []
    for i in range(1, 11):
        parts.append(f"## {i}. Section {i}\n\nContent for section {i}. " + ("x" * 60))
    text = "\n\n".join(parts)
    with pytest.raises(DesignSectionParseError) as exc_info:
        parse_design_md(text)
    assert 11 in exc_info.value.missing


def test_non_contiguous_sections_raises() -> None:
    # Skip section 5 — provide 1-4, 6-12
    parts = []
    for i in list(range(1, 5)) + list(range(6, 13)):
        parts.append(f"## {i}. Section {i}\n\nContent for section {i}. " + ("x" * 60))
    text = "\n\n".join(parts)
    with pytest.raises(DesignSectionParseError):
        parse_design_md(text)


def test_section_2_no_hex_raises() -> None:
    """Section 2 without any hex color must raise DesignSectionValidationError."""
    parts = []
    for i in range(1, 12):
        if i == 2:
            content = "Primary: blue. Accent: red."  # no hex
        elif i == 11:
            content = "A" * 210  # enough chars
        else:
            content = "x" * 60
        parts.append(f"## {i}. Section {i}\n\n{content}")
    text = "\n\n".join(parts)
    with pytest.raises(DesignSectionValidationError):
        parse_design_md(text)


def test_section_11_too_short_raises() -> None:
    """Section 11 with < 200 chars must raise DesignSectionValidationError."""
    parts = []
    for i in range(1, 12):
        if i == 2:
            content = "Primary: #123456"
        elif i == 11:
            content = "Too short."  # < 200 chars
        else:
            content = "x" * 60
        parts.append(f"## {i}. Section {i}\n\n{content}")
    text = "\n\n".join(parts)
    with pytest.raises(DesignSectionValidationError):
        parse_design_md(text)


# ---------------------------------------------------------------------------
# extract_css_vars
# ---------------------------------------------------------------------------


def test_extract_css_vars_returns_root_block(fixture_sections: list[DesignSection]) -> None:
    css = extract_css_vars(fixture_sections)
    assert css.startswith(":root {")
    assert css.strip().endswith("}")


def test_extract_css_vars_contains_color_primary(fixture_sections: list[DesignSection]) -> None:
    css = extract_css_vars(fixture_sections)
    assert "--color-primary" in css


def test_extract_css_vars_contains_font_display(fixture_sections: list[DesignSection]) -> None:
    css = extract_css_vars(fixture_sections)
    assert "--font-display" in css


def test_extract_css_vars_empty_sections() -> None:
    assert extract_css_vars([]) == ""


# ---------------------------------------------------------------------------
# extract_layout_css
# ---------------------------------------------------------------------------


def test_extract_layout_css_contains_hero(fixture_sections: list[DesignSection]) -> None:
    css = extract_layout_css(fixture_sections)
    assert ".layout-hero-title" in css


def test_extract_layout_css_contains_stat(fixture_sections: list[DesignSection]) -> None:
    css = extract_layout_css(fixture_sections)
    assert ".layout-stat-highlight" in css


def test_extract_layout_css_uses_css_vars(fixture_sections: list[DesignSection]) -> None:
    css = extract_layout_css(fixture_sections)
    assert "var(--color-" in css or "var(--font-" in css


def test_extract_layout_css_no_script_tag(fixture_sections: list[DesignSection]) -> None:
    css = extract_layout_css(fixture_sections)
    assert "<script" not in css.lower()
