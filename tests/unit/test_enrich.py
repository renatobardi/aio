"""Unit tests for Phase 2 Image Enrichment — _enrich.py (T041).

TDD: all tests should FAIL before T043–T052 are implemented.
"""


# ---------------------------------------------------------------------------
# T041-A: EnrichContext dataclass
# ---------------------------------------------------------------------------


class TestEnrichContext:
    def test_importable(self):
        from aio._enrich import EnrichContext

        assert EnrichContext is not None

    def test_is_dataclass(self):
        import dataclasses

        from aio._enrich import EnrichContext

        assert dataclasses.is_dataclass(EnrichContext)

    def test_required_fields(self):
        import dataclasses

        from aio._enrich import EnrichContext

        field_names = {f.name for f in dataclasses.fields(EnrichContext)}
        assert "slide_index" in field_names
        assert "prompt" in field_names
        assert "seed" in field_names
        assert "image_bytes" in field_names
        assert "is_placeholder" in field_names

    def test_construction(self):
        from aio._enrich import EnrichContext

        ctx = EnrichContext(
            slide_index=1,
            prompt="An AI-powered presentation",
            seed=42,
            image_bytes=None,
            is_placeholder=False,
        )
        assert ctx.slide_index == 1
        assert ctx.prompt == "An AI-powered presentation"
        assert ctx.seed == 42
        assert ctx.image_bytes is None
        assert ctx.is_placeholder is False

    def test_error_message_field_optional(self):
        from aio._enrich import EnrichContext

        ctx = EnrichContext(
            slide_index=0,
            prompt="test",
            seed=0,
            image_bytes=None,
            is_placeholder=True,
        )
        # error_message should default to None
        assert ctx.error_message is None


# ---------------------------------------------------------------------------
# T041-B: infer_prompt()
# ---------------------------------------------------------------------------


class TestInferPrompt:
    def test_importable(self):
        from aio._enrich import infer_prompt

        assert callable(infer_prompt)

    def test_basic_concatenation(self):
        from aio._enrich import infer_prompt

        result = infer_prompt("AI Presentations", "Create slides with Claude.")
        assert "AI Presentations" in result

    def test_truncates_to_100_chars(self):
        from aio._enrich import infer_prompt

        long_body = "x" * 200
        result = infer_prompt("Title", long_body)
        assert len(result) <= 100

    def test_fallback_when_result_too_short(self):
        from aio._enrich import infer_prompt

        result = infer_prompt(None, "")
        assert result == "Abstract presentation slide"

    def test_fallback_when_body_is_whitespace(self):
        from aio._enrich import infer_prompt

        result = infer_prompt(None, "   ")
        assert result == "Abstract presentation slide"

    def test_strips_html_tags(self):
        from aio._enrich import infer_prompt

        result = infer_prompt("Title", "<p>Clean <strong>text</strong> here</p>")
        assert "<p>" not in result
        assert "<strong>" not in result
        assert "Clean" in result

    def test_none_title_uses_body_only(self):
        from aio._enrich import infer_prompt

        result = infer_prompt(None, "A compelling slide about machine learning.")
        assert "machine learning" in result

    def test_short_combined_result_falls_back(self):
        from aio._enrich import infer_prompt

        # Title + body together < 3 chars after strip → fallback
        result = infer_prompt("", "  ")
        assert result == "Abstract presentation slide"


# ---------------------------------------------------------------------------
# T041-C: derive_seed()
# ---------------------------------------------------------------------------


class TestDeriveSeed:
    def test_importable(self):
        from aio._enrich import derive_seed

        assert callable(derive_seed)

    def test_returns_int(self):
        from aio._enrich import derive_seed

        result = derive_seed("My Deck", 1)
        assert isinstance(result, int)

    def test_deterministic(self):
        from aio._enrich import derive_seed

        assert derive_seed("My Deck", 1) == derive_seed("My Deck", 1)

    def test_different_slides_different_seeds(self):
        from aio._enrich import derive_seed

        assert derive_seed("My Deck", 1) != derive_seed("My Deck", 2)

    def test_different_deck_titles_different_seeds(self):
        from aio._enrich import derive_seed

        assert derive_seed("Deck A", 1) != derive_seed("Deck B", 1)

    def test_seed_is_positive(self):
        from aio._enrich import derive_seed

        assert derive_seed("Test", 0) >= 0


# ---------------------------------------------------------------------------
# T041-D: JPEG validation
# ---------------------------------------------------------------------------


class TestJpegValidation:
    def test_valid_jpeg_magic_bytes_accepted(self):
        # Load actual mock JPEG
        import pathlib

        jpeg_path = pathlib.Path(__file__).parent.parent / "fixtures" / "mock_pollinations_response.jpg"
        if jpeg_path.exists():
            valid_jpeg = jpeg_path.read_bytes()
            assert valid_jpeg[:3] == b"\xff\xd8\xff"

    def test_invalid_bytes_detected(self):
        from aio._enrich import _is_valid_jpeg

        assert _is_valid_jpeg(b"NOTAJPEG") is False

    def test_valid_jpeg_magic_detected(self):
        from aio._enrich import _is_valid_jpeg

        assert _is_valid_jpeg(b"\xff\xd8\xff\xe0fake") is True

    def test_empty_bytes_invalid(self):
        from aio._enrich import _is_valid_jpeg

        assert _is_valid_jpeg(b"") is False

    def test_too_short_bytes_invalid(self):
        from aio._enrich import _is_valid_jpeg

        assert _is_valid_jpeg(b"\xff\xd8") is False


# ---------------------------------------------------------------------------
# T041-E: make_placeholder_svg()
# ---------------------------------------------------------------------------


class TestMakePlaceholderSvg:
    def test_importable(self):
        from aio._enrich import make_placeholder_svg

        assert callable(make_placeholder_svg)

    def test_returns_svg_string(self):
        from aio._enrich import make_placeholder_svg

        svg = make_placeholder_svg()
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_under_200_bytes(self):
        from aio._enrich import make_placeholder_svg

        svg = make_placeholder_svg()
        assert len(svg.encode("utf-8")) < 200

    def test_no_external_resources(self):
        import re

        from aio._enrich import make_placeholder_svg

        svg = make_placeholder_svg()
        # Must not have any src= or href= pointing to an external URL
        external = re.findall(r'(?:src|href)=["\']https?://', svg)
        assert external == []
