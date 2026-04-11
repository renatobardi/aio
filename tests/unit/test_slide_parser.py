"""Tests for the slide parser: SlideAST, parse_slides() (US4)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest


class TestSlideASTDataclass:
    """SlideAST is a dataclass with expected fields."""

    def test_slideast_has_required_fields(self) -> None:
        from aio.commands.build import SlideAST

        slide = SlideAST(
            index=0,
            frontmatter={"title": "Test"},
            title="Test",
            body_tokens=[],
            metadata={},
            raw_markdown="# Test",
        )
        assert slide.index == 0
        assert slide.frontmatter == {"title": "Test"}
        assert slide.title == "Test"
        assert slide.body_tokens == []
        assert slide.metadata == {}
        assert slide.raw_markdown == "# Test"


class TestParseSlides:
    """parse_slides() parses a 3-slide markdown file correctly."""

    def test_3_slides_returns_3_objects(self, sample_slides_md: str, tmp_path: Path) -> None:
        from aio.commands.build import parse_slides

        slides_path = tmp_path / "slides.md"
        slides_path.write_text(sample_slides_md, encoding="utf-8")
        slides = parse_slides(slides_path)
        assert len(slides) == 3

    def test_frontmatter_extracted(self, sample_slides_md: str, tmp_path: Path) -> None:
        from aio.commands.build import parse_slides

        slides_path = tmp_path / "slides.md"
        slides_path.write_text(sample_slides_md, encoding="utf-8")
        slides = parse_slides(slides_path)
        # All slides share the deck frontmatter
        assert slides[0].frontmatter.get("title") == "Test Deck"
        assert slides[0].frontmatter.get("agent") == "claude"
        assert slides[0].frontmatter.get("theme") == "minimal"

    def test_metadata_tags_extracted(self, sample_slides_md: str, tmp_path: Path) -> None:
        from aio.commands.build import parse_slides

        slides_path = tmp_path / "slides.md"
        slides_path.write_text(sample_slides_md, encoding="utf-8")
        slides = parse_slides(slides_path)
        # Slide 0 has @layout: hero-title and @title: Welcome
        assert slides[0].metadata.get("layout") == "hero-title"
        assert slides[0].metadata.get("title") == "Welcome"

    def test_slide_indices_are_sequential(self, sample_slides_md: str, tmp_path: Path) -> None:
        from aio.commands.build import parse_slides

        slides_path = tmp_path / "slides.md"
        slides_path.write_text(sample_slides_md, encoding="utf-8")
        slides = parse_slides(slides_path)
        for i, slide in enumerate(slides):
            assert slide.index == i

    def test_title_extracted_from_heading(self, sample_slides_md: str, tmp_path: Path) -> None:
        from aio.commands.build import parse_slides

        slides_path = tmp_path / "slides.md"
        slides_path.write_text(sample_slides_md, encoding="utf-8")
        slides = parse_slides(slides_path)
        assert slides[0].title == "Slide 1"
        assert slides[1].title == "Slide 2"

    def test_metadata_tags_removed_from_content(self, sample_slides_md: str, tmp_path: Path) -> None:
        from aio.commands.build import parse_slides

        slides_path = tmp_path / "slides.md"
        slides_path.write_text(sample_slides_md, encoding="utf-8")
        slides = parse_slides(slides_path)
        # The raw_markdown should not contain the @layout tag
        assert "<!-- @layout:" not in slides[0].raw_markdown


class TestMetadataTagParsing:
    """_extract_metadata parses various tag formats."""

    def test_icon_color_data_tags(self, tmp_path: Path) -> None:
        from aio.commands.build import parse_slides

        content = """\
---
title: Test
agent: claude
theme: minimal
---

# Slide 1

<!-- @icon: brain -->
<!-- @color: #FF5733 -->
<!-- @data: 2024:50, 2025:75 -->

Body text.
"""
        slides_path = tmp_path / "slides.md"
        slides_path.write_text(content, encoding="utf-8")
        slides = parse_slides(slides_path)
        assert slides[0].metadata.get("icon") == "brain"
        assert slides[0].metadata.get("color") == "#FF5733"
        assert slides[0].metadata.get("data") == "2024:50, 2025:75"

    def test_malformed_empty_key_ignored(self, tmp_path: Path, caplog) -> None:
        from aio.commands.build import parse_slides

        content = """\
---
title: Test
agent: claude
theme: minimal
---

# Slide 1

<!-- @: invalid -->

Body.
"""
        slides_path = tmp_path / "slides.md"
        slides_path.write_text(content, encoding="utf-8")
        # Should not raise, malformed tag silently ignored
        slides = parse_slides(slides_path)
        assert len(slides) == 1

    def test_unknown_layout_stored_with_warning(self, tmp_path: Path) -> None:
        from aio.commands.build import parse_slides

        content = """\
---
title: Test
agent: claude
theme: minimal
---

# Slide 1

<!-- @layout: nonexistent -->

Body.
"""
        slides_path = tmp_path / "slides.md"
        slides_path.write_text(content, encoding="utf-8")
        # Should not raise — layout validation happens at build time, not parse time
        slides = parse_slides(slides_path)
        assert slides[0].metadata.get("layout") == "nonexistent"


class TestParserEdgeCases:
    """Parser handles edge cases gracefully."""

    def test_invalid_yaml_raises_parse_error(self, tmp_path: Path) -> None:
        from aio.commands.build import parse_slides
        from aio.exceptions import ParseError

        content = """\
---
title: [invalid yaml
---

# Slide 1

Body.
"""
        slides_path = tmp_path / "slides.md"
        slides_path.write_text(content, encoding="utf-8")
        with pytest.raises(ParseError):
            parse_slides(slides_path)

    def test_100_slides_under_50ms(self, tmp_path: Path) -> None:
        from aio.commands.build import parse_slides

        slides_body = "\n---\n\n# Slide {i}\n\n<!-- @layout: content -->\n\nContent {i}.\n"
        content = "---\ntitle: Big Deck\nagent: claude\ntheme: minimal\n---\n"
        content += "".join(slides_body.format(i=i) for i in range(100))
        slides_path = tmp_path / "slides.md"
        slides_path.write_text(content, encoding="utf-8")

        start = time.perf_counter()
        slides = parse_slides(slides_path)
        elapsed = time.perf_counter() - start

        assert len(slides) == 100
        assert elapsed < 0.050, f"Parsing 100 slides took {elapsed:.4f}s — must be < 50ms"
