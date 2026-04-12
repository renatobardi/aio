"""Unit tests for inline metadata extraction (Phase 2 — T003).

Tests for extract_inline_metadata() and InlineMetadata dataclass.
TDD: all tests in this file should FAIL before T004/T005/T006 are implemented.
"""

import pytest

from aio.composition.metadata import InlineMetadata, extract_inline_metadata


class TestInlineMetadataDataclass:
    def test_construction_valid(self):
        meta = InlineMetadata(key="icon", value="brain", line=1)
        assert meta.key == "icon"
        assert meta.value == "brain"
        assert meta.line == 1

    def test_immutable(self):
        meta = InlineMetadata(key="icon", value="brain", line=1)
        with pytest.raises((AttributeError, TypeError)):
            meta.key = "changed"  # type: ignore[misc]


class TestExtractInlineMetadata:
    def test_basic_extraction(self):
        body = "<!-- @icon: brain -->\n# Title"
        metadata, cleaned = extract_inline_metadata(body)
        assert metadata["icon"] == "brain"
        assert "<!-- @icon:" not in cleaned

    def test_comment_removed_from_body(self):
        body = "<!-- @icon: brain -->\n# Title\n\nSome text."
        _, cleaned = extract_inline_metadata(body)
        assert "<!--" not in cleaned
        assert "# Title" in cleaned
        assert "Some text." in cleaned

    def test_multiple_keys(self):
        body = "<!-- @icon: brain -->\n<!-- @icon-size: 64px -->\n<!-- @icon-color: #635BFF -->"
        metadata, _ = extract_inline_metadata(body)
        assert metadata["icon"] == "brain"
        assert metadata["icon-size"] == "64px"
        assert metadata["icon-color"] == "#635BFF"

    def test_case_insensitive_keys(self):
        body = "<!-- @ICON: brain -->\n<!-- @Icon-Size: 64px -->"
        metadata, _ = extract_inline_metadata(body)
        assert "icon" in metadata
        assert "icon-size" in metadata

    def test_special_chars_in_value(self):
        body = "<!-- @icon-color: #635BFF -->"
        metadata, _ = extract_inline_metadata(body)
        assert metadata["icon-color"] == "#635BFF"

    def test_multi_word_value(self):
        body = "<!-- @image-prompt: A futuristic AI brain with circuits glowing blue -->"
        metadata, _ = extract_inline_metadata(body)
        assert metadata["image-prompt"] == "A futuristic AI brain with circuits glowing blue"

    def test_comma_separated_value(self):
        body = "<!-- @data: Q1:50, Q2:75, Q3:90 -->"
        metadata, _ = extract_inline_metadata(body)
        assert metadata["data"] == "Q1:50, Q2:75, Q3:90"

    def test_empty_body(self):
        metadata, cleaned = extract_inline_metadata("")
        assert metadata == {}
        assert cleaned == ""

    def test_no_tags(self):
        body = "# Title\n\nSome text."
        metadata, cleaned = extract_inline_metadata(body)
        assert metadata == {}
        assert cleaned == body

    def test_malformed_comment_ignored(self):
        body = "<!-- not a tag -->\n<!-- @valid: yes -->"
        metadata, cleaned = extract_inline_metadata(body)
        assert "valid" in metadata
        assert metadata["valid"] == "yes"

    def test_frontmatter_wins_on_conflict(self):
        """When merging into SlideAST.metadata, YAML frontmatter keys win."""
        # The extract_inline_metadata function itself returns the HTML comment keys.
        # The caller (parse_slides) is responsible for frontmatter-wins precedence.
        # Here we test the raw extractor returns the comment value.
        body = "<!-- @layout: hero-title -->"
        metadata, _ = extract_inline_metadata(body)
        assert metadata["layout"] == "hero-title"

    def test_value_with_calc_expression(self):
        body = "<!-- @height: calc(100% - 20px) -->"
        metadata, _ = extract_inline_metadata(body)
        assert metadata["height"] == "calc(100% - 20px)"

    def test_value_stripped(self):
        body = "<!-- @icon:   brain   -->"
        metadata, _ = extract_inline_metadata(body)
        assert metadata["icon"] == "brain"

    def test_key_lowercased(self):
        body = "<!-- @CHART: bar -->"
        metadata, _ = extract_inline_metadata(body)
        assert "chart" in metadata
        assert "CHART" not in metadata
