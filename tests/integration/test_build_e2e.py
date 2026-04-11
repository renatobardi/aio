"""Integration tests for the build pipeline v2 (T043)."""

from __future__ import annotations

from pathlib import Path

from aio._validators import check_external_urls
from aio.commands.build import build_pipeline, parse_slides

FIXTURE_SLIDES = Path(__file__).parent.parent / "fixtures" / "slides" / "sample_all_layouts.md"
FIXTURE_THEME_DIR = Path(__file__).parent.parent / "fixtures" / "themes" / "fixture_theme"

# The 8 core M1 layouts expected in sample_all_layouts.md
EXPECTED_LAYOUTS = {
    "hero-title",
    "stat-highlight",
    "split-image-text",
    "content-with-icons",
    "comparison-2col",
    "quote",
    "key-takeaways",
    "closing",
}


# ---------------------------------------------------------------------------
# parse_slides
# ---------------------------------------------------------------------------


def test_parse_slides_returns_10_slides() -> None:
    slides = parse_slides(FIXTURE_SLIDES)
    assert len(slides) == 10


def test_parse_slides_first_slide_has_hero_layout() -> None:
    slides = parse_slides(FIXTURE_SLIDES)
    assert slides[0].metadata.get("layout") == "hero-title"


def test_parse_slides_extracts_stat_metadata() -> None:
    slides = parse_slides(FIXTURE_SLIDES)
    stat_slide = slides[1]
    assert stat_slide.metadata.get("stat") == "87%"
    assert stat_slide.metadata.get("label") == "Accuracy"


# ---------------------------------------------------------------------------
# build_pipeline (full pipeline)
# ---------------------------------------------------------------------------


def test_build_pipeline_creates_output_file(tmp_path: Path) -> None:
    out = tmp_path / "output.html"
    result = build_pipeline(FIXTURE_SLIDES, output=out, theme_id="minimal")
    assert out.exists()
    assert out.stat().st_size > 0
    assert result.slide_count == 10


def test_build_pipeline_no_external_urls(tmp_path: Path) -> None:
    out = tmp_path / "output.html"
    build_pipeline(FIXTURE_SLIDES, output=out, theme_id="minimal")
    html = out.read_text(encoding="utf-8")
    external = check_external_urls(html)
    assert external == [], f"External URLs found: {external}"


def test_build_pipeline_all_8_data_layout_values_present(tmp_path: Path) -> None:
    out = tmp_path / "output.html"
    build_pipeline(FIXTURE_SLIDES, output=out, theme_id="minimal")
    html = out.read_text(encoding="utf-8")
    for layout in EXPECTED_LAYOUTS:
        assert f'data-layout="{layout}"' in html, f"Missing data-layout={layout!r} in output"


def test_build_pipeline_dry_run_does_not_write(tmp_path: Path) -> None:
    out = tmp_path / "output.html"
    result = build_pipeline(FIXTURE_SLIDES, output=out, theme_id="minimal", dry_run=True)
    assert not out.exists(), "dry_run must not write the output file"
    assert result.slide_count == 10


def test_build_pipeline_returns_build_result(tmp_path: Path) -> None:
    from aio.composition.metadata import BuildResult

    out = tmp_path / "output.html"
    result = build_pipeline(FIXTURE_SLIDES, output=out, theme_id="minimal")
    assert isinstance(result, BuildResult)
    assert result.byte_size > 0
    assert result.elapsed_seconds >= 0.0
    assert result.theme_id == "minimal"


def test_build_pipeline_layout_histogram(tmp_path: Path) -> None:
    out = tmp_path / "output.html"
    result = build_pipeline(FIXTURE_SLIDES, output=out, theme_id="minimal")
    # hero-title should appear exactly once
    assert result.layout_histogram.get("hero-title", 0) >= 1


def test_build_pipeline_unknown_layout_falls_back_to_content(tmp_path: Path) -> None:
    """A slide with an unknown @layout tag should fall back to content, not crash."""
    slides_md = tmp_path / "slides.md"
    slides_md.write_text(
        "---\ntitle: Test\ntheme: minimal\nagent: claude\n---\n\n"
        "<!-- @layout: galaxy-brain -->\n# Unknown layout slide\n",
        encoding="utf-8",
    )
    out = tmp_path / "output.html"
    result = build_pipeline(slides_md, output=out, theme_id="minimal")
    assert result.slide_count == 1
    html = out.read_text(encoding="utf-8")
    assert 'data-layout="content"' in html


def test_build_pipeline_html_contains_reveal_js(tmp_path: Path) -> None:
    out = tmp_path / "output.html"
    build_pipeline(FIXTURE_SLIDES, output=out, theme_id="minimal")
    html = out.read_text(encoding="utf-8")
    # Reveal.js initializer is present
    assert "Reveal" in html or "reveal" in html.lower()


def test_build_pipeline_no_script_tag_in_slides(tmp_path: Path) -> None:
    """No user-injected <script> tags should appear in individual slide sections."""
    slides_md = tmp_path / "slides.md"
    slides_md.write_text(
        "---\ntitle: XSS Test\ntheme: minimal\nagent: claude\n---\n\n"
        "<!-- @layout: content -->\n<script>alert('xss')</script>\n",
        encoding="utf-8",
    )
    out = tmp_path / "output.html"
    build_pipeline(slides_md, output=out, theme_id="minimal")
    html = out.read_text(encoding="utf-8")
    # The section wrapper must not contain a live <script> tag
    import re

    sections = re.findall(r"<section[^>]*data-layout[^>]*>.*?</section>", html, re.DOTALL)  # NOSONAR: test-only, applied to known-size fixture HTML
    for section in sections:
        assert "<script" not in section.lower(), "Section must not contain <script>"
