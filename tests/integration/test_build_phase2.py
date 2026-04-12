"""Integration tests for AIO Phase 2 — Visual Enrichment (T011, T021, T032, T054, T055).

TDD: tests are written first and should FAIL before the corresponding implementations.
Each test class maps to a specific task/user story.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import pytest

from aio._validators import check_external_urls

FIXTURE_PHASE2 = Path(__file__).parent.parent / "fixtures" / "slides_phase2.md"
FIXTURE_MINIMAL_DESIGN_MD = Path(__file__).resolve().parents[2] / "src" / "aio" / "themes" / "minimal" / "DESIGN.md"

# ---------------------------------------------------------------------------
# T011 — US1: Icon library integration
# ---------------------------------------------------------------------------


class TestIconIntegration:
    def test_icon_directive_inlines_svg(self, tmp_path: Path) -> None:
        """Build a slide with @icon: brain and assert icon-brain SVG is in output."""
        from aio.commands.build import build_pipeline

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Icon Test\ntheme: minimal\n---\n\n"
            "<!-- @icon: brain -->\n\n# AI Insights\n\nBody text.",
            encoding="utf-8",
        )
        out = tmp_path / "out.html"
        build_pipeline(slides, output=out, theme_id="minimal")
        html = out.read_text(encoding="utf-8")
        assert "icon-brain" in html, "Expected icon-brain in output HTML"

    def test_icon_no_external_urls(self, tmp_path: Path) -> None:
        from aio.commands.build import build_pipeline

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Icon Test\ntheme: minimal\n---\n\n"
            "<!-- @icon: brain -->\n\n# Title",
            encoding="utf-8",
        )
        out = tmp_path / "out.html"
        build_pipeline(slides, output=out, theme_id="minimal")
        html = out.read_text(encoding="utf-8")
        bad = re.findall(r'(?:href|src)=["\']https?://[^"\']+["\']', html)
        assert not bad, f"External URLs found: {bad}"


# ---------------------------------------------------------------------------
# T021 — US2: DataViz integration (bar, donut, sparkline, timeline)
# ---------------------------------------------------------------------------


class TestDataVizIntegration:
    def test_four_chart_types_produce_svg(self, tmp_path: Path) -> None:
        from aio.commands.build import build_pipeline

        slides = tmp_path / "slides.md"
        content = (
            "---\ntitle: Chart Test\ntheme: minimal\n---\n\n"
            "<!-- @chart: bar -->\n<!-- @data: Q1:50, Q2:75 -->\n\n# Bar\n\n---\n\n"
            "<!-- @chart: donut -->\n<!-- @data: A:40, B:60 -->\n\n# Donut\n\n---\n\n"
            "<!-- @chart: sparkline -->\n<!-- @data: 10, 20, 15, 30 -->\n\n# Sparkline\n\n---\n\n"
            "<!-- @chart: timeline -->\n<!-- @data: 2020-01: Alpha\n2021-06: Beta -->\n\n# Timeline"
        )
        slides.write_text(content, encoding="utf-8")
        out = tmp_path / "out.html"
        build_pipeline(slides, output=out, theme_id="minimal")
        html = out.read_text(encoding="utf-8")
        svg_count = len(re.findall(r"<svg[^>]*>", html))
        assert svg_count >= 4, f"Expected ≥ 4 SVG elements, found {svg_count}"

    def test_no_external_urls_in_chart_output(self, tmp_path: Path) -> None:
        from aio.commands.build import build_pipeline

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Chart Test\ntheme: minimal\n---\n\n"
            "<!-- @chart: bar -->\n<!-- @data: A:10, B:20 -->\n\n# Bar",
            encoding="utf-8",
        )
        out = tmp_path / "out.html"
        build_pipeline(slides, output=out, theme_id="minimal")
        html = out.read_text(encoding="utf-8")
        bad = re.findall(r'(?:href|src)=["\']https?://[^"\']+["\']', html)
        assert not bad

    def test_bar_chart_deterministic(self, tmp_path: Path) -> None:
        from aio.commands.build import build_pipeline

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Det Test\ntheme: minimal\n---\n\n"
            "<!-- @chart: bar -->\n<!-- @data: Q1:50, Q2:75 -->\n\n# Bar",
            encoding="utf-8",
        )
        out1 = tmp_path / "out1.html"
        out2 = tmp_path / "out2.html"
        build_pipeline(slides, output=out1, theme_id="minimal")
        build_pipeline(slides, output=out2, theme_id="minimal")
        # Extract SVG from both outputs
        html1 = out1.read_text(encoding="utf-8")
        html2 = out2.read_text(encoding="utf-8")
        svgs1 = re.findall(r"<svg[\s\S]*?</svg>", html1)
        svgs2 = re.findall(r"<svg[\s\S]*?</svg>", html2)
        assert svgs1 == svgs2, "Bar chart SVG is not deterministic across two builds"


# ---------------------------------------------------------------------------
# T032 — US3: CSS Decorations integration
# ---------------------------------------------------------------------------


class TestDecorationIntegration:
    def test_decoration_class_on_section(self, tmp_path: Path) -> None:
        """Build with section 12 in DESIGN.md; assert decoration class on <section>."""
        from aio.commands.build import build_pipeline

        # Copy minimal theme DESIGN.md to temp dir and append section 12
        design_src = FIXTURE_MINIMAL_DESIGN_MD
        assert design_src.exists(), f"Minimal DESIGN.md not found at {design_src}"
        design_content = design_src.read_text(encoding="utf-8")
        section12 = (
            "\n\n## 12. Decorations\n\n"
            "### Gradients\n"
            "- Primary Gradient: linear-gradient(135deg, #635BFF 0%, #00D084 100%)\n\n"
            "### Dividers\n"
            "- Thin: 1px solid var(--color-neutral-300)\n\n"
            "### Glow Effects\n"
            "- Primary Glow: 0 0 30px rgba(99, 91, 255, 0.5)\n\n"
            "### Accent Lines\n"
            "- Left Border: 4px solid var(--color-primary)\n"
        )
        modified_design = design_content + section12
        theme_dir = tmp_path / "theme_with_dec"
        theme_dir.mkdir()

        # Copy entire minimal theme
        import shutil
        for f in design_src.parent.iterdir():
            if f.is_file():
                shutil.copy(f, theme_dir / f.name)
        (theme_dir / "DESIGN.md").write_text(modified_design, encoding="utf-8")

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Dec Test\ntheme: minimal\n---\n\n"
            "<!-- @decoration: gradient -->\n\n# Bold Statement\n\nText.",
            encoding="utf-8",
        )
        out = tmp_path / "out.html"
        build_pipeline(slides, output=out, theme_id="minimal", theme_dir=theme_dir)
        html = out.read_text(encoding="utf-8")
        assert "decoration-gradient-primary" in html

    def test_decoration_css_in_style_block(self, tmp_path: Path) -> None:
        from aio.commands.build import build_pipeline
        import shutil

        design_src = FIXTURE_MINIMAL_DESIGN_MD
        design_content = design_src.read_text(encoding="utf-8")
        section12 = (
            "\n\n## 12. Decorations\n\n"
            "### Gradients\n"
            "- Primary Gradient: linear-gradient(135deg, #635BFF 0%, #00D084 100%)\n"
        )
        theme_dir = tmp_path / "theme_with_dec2"
        theme_dir.mkdir()
        for f in design_src.parent.iterdir():
            if f.is_file():
                shutil.copy(f, theme_dir / f.name)
        (theme_dir / "DESIGN.md").write_text(design_content + section12, encoding="utf-8")

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: CSS Test\ntheme: minimal\n---\n\n"
            "<!-- @decoration: gradient -->\n\n# Title",
            encoding="utf-8",
        )
        out = tmp_path / "out.html"
        build_pipeline(slides, output=out, theme_id="minimal", theme_dir=theme_dir)
        html = out.read_text(encoding="utf-8")
        assert ".decoration-gradient-primary" in html

    def test_no_external_urls(self, tmp_path: Path) -> None:
        from aio.commands.build import build_pipeline

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Dec Test\ntheme: minimal\n---\n\n"
            "<!-- @decoration: gradient -->\n\n# Title",
            encoding="utf-8",
        )
        out = tmp_path / "out.html"
        build_pipeline(slides, output=out, theme_id="minimal")
        html = out.read_text(encoding="utf-8")
        bad = re.findall(r'(?:href|src)=["\']https?://[^"\']+["\']', html)
        assert not bad


# ---------------------------------------------------------------------------
# T054 — US5: Combined Phase 2 deck integration
# ---------------------------------------------------------------------------


class TestCombinedPhase2Integration:
    def test_combined_deck_builds_successfully(self, tmp_path: Path) -> None:
        from aio.commands.build import build_pipeline

        out = tmp_path / "out.html"
        build_pipeline(FIXTURE_PHASE2, output=out, theme_id="minimal")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_combined_deck_build_time_under_2s(self, tmp_path: Path) -> None:
        from aio.commands.build import build_pipeline

        out = tmp_path / "out.html"
        start = time.perf_counter()
        build_pipeline(FIXTURE_PHASE2, output=out, theme_id="minimal")
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"Build took {elapsed:.2f}s, expected < 2s"

    def test_combined_deck_no_external_urls(self, tmp_path: Path) -> None:
        from aio.commands.build import build_pipeline

        out = tmp_path / "out.html"
        build_pipeline(FIXTURE_PHASE2, output=out, theme_id="minimal")
        html = out.read_text(encoding="utf-8")
        bad = re.findall(r'(?:href|src)=["\']https?://[^"\']+["\']', html)
        assert not bad

    def test_dry_run_completes_fast_and_no_output(self, tmp_path: Path) -> None:
        import time as _time
        from aio.commands.build import build_pipeline

        out = tmp_path / "out.html"
        start = _time.perf_counter()
        build_pipeline(FIXTURE_PHASE2, output=out, theme_id="minimal", dry_run=True)
        elapsed = (_time.perf_counter() - start) * 1000
        assert elapsed < 100, f"dry-run took {elapsed:.1f}ms, expected < 100ms"
        assert not out.exists(), "dry-run must not create output file"


# ---------------------------------------------------------------------------
# T055 — US5: Phase 1 regression test
# ---------------------------------------------------------------------------


class TestPhase1Regression:
    def test_plain_deck_no_phase2_artifacts(self, tmp_path: Path) -> None:
        """A plain Phase 1 deck (no Phase 2 directives) must not gain decoration CSS,
        icon containers, or chart SVGs from Phase 2 code paths."""
        from aio.commands.build import build_pipeline

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Plain Deck\ntheme: minimal\n---\n\n"
            "# Hello World\n\nThis is a plain slide with no Phase 2 directives.",
            encoding="utf-8",
        )
        out = tmp_path / "out.html"
        build_pipeline(slides, output=out, theme_id="minimal")
        html = out.read_text(encoding="utf-8")
        assert "icon-container" not in html
        assert "decoration-gradient" not in html
        assert "chart-svg" not in html
