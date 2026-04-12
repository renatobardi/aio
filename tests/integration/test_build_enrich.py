"""Integration tests for Phase 2 image enrichment — aio build --enrich (T042).

TDD: all tests should FAIL before T043–T052 are implemented.
"""

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

import pytest

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"
MOCK_JPEG = FIXTURES / "mock_pollinations_response.jpg"


def _mock_urlopen(url, timeout=30):
    """Return a file-like object with the mock JPEG bytes."""
    data = MOCK_JPEG.read_bytes()
    mock_resp = MagicMock()
    mock_resp.read.return_value = data
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestEnrichIntegration:
    def test_base64_jpeg_in_output(self, tmp_path: pathlib.Path) -> None:
        from aio.commands.build import build_pipeline

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Enrich Test\n---\n\n"
            "<!-- @image-prompt: A futuristic AI brain glowing blue -->\n\n"
            "# AI Intelligence\n\nCutting-edge insights.",
            encoding="utf-8",
        )
        out = tmp_path / "out.html"

        with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
            build_pipeline(slides, output=out, enrich=True)

        html = out.read_text(encoding="utf-8")
        assert 'data:image/jpeg;base64,' in html

    def test_no_external_urls_after_enrich(self, tmp_path: pathlib.Path) -> None:
        from aio.commands.build import build_pipeline

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Enrich No URLs\n---\n\n"
            "<!-- @image-prompt: Minimal blue gradient -->\n\n"
            "# Title\n\nContent.",
            encoding="utf-8",
        )
        out = tmp_path / "out.html"

        with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
            build_pipeline(slides, output=out, enrich=True)

        html = out.read_text(encoding="utf-8")
        import re
        external = re.findall(r'(?:href|src)=["\']( https?://[^"\']+)["\']', html)
        assert external == [], f"External URLs found: {external}"

    def test_deterministic_with_enrich(self, tmp_path: pathlib.Path) -> None:
        from aio.commands.build import build_pipeline

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Det Test\n---\n\n"
            "<!-- @image-prompt: A circle on white -->\n\n"
            "# Slide\n\nBody.",
            encoding="utf-8",
        )
        out1 = tmp_path / "out1.html"
        out2 = tmp_path / "out2.html"

        with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
            build_pipeline(slides, output=out1, enrich=True)
        with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
            build_pipeline(slides, output=out2, enrich=True)

        assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")

    def test_api_failure_uses_placeholder(self, tmp_path: pathlib.Path) -> None:
        import urllib.error
        from aio.commands.build import build_pipeline

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Fallback Test\n---\n\n"
            "<!-- @image-prompt: Test prompt -->\n\n"
            "# Slide\n\nBody.",
            encoding="utf-8",
        )
        out = tmp_path / "out.html"

        def _failing_urlopen(url, timeout=30):
            raise urllib.error.URLError("simulated API failure")

        with patch("urllib.request.urlopen", side_effect=_failing_urlopen):
            build_pipeline(slides, output=out, enrich=True)

        html = out.read_text(encoding="utf-8")
        assert "<svg" in html  # placeholder SVG rendered
        assert out.exists()

    def test_warning_logged_on_api_failure(self, tmp_path: pathlib.Path) -> None:
        import logging
        import urllib.error
        from unittest.mock import patch as mock_patch
        from aio.commands.build import build_pipeline
        import aio._enrich as enrich_module

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Warn Test\n---\n\n"
            "<!-- @image-prompt: test -->\n\n"
            "# Title\n\nText.",
            encoding="utf-8",
        )
        out = tmp_path / "out.html"

        def _failing_urlopen(url, timeout=30):
            raise urllib.error.URLError("timeout")

        with mock_patch("urllib.request.urlopen", side_effect=_failing_urlopen):
            with mock_patch.object(enrich_module._log, "warning") as mock_warn:
                build_pipeline(slides, output=out, enrich=True)
        assert mock_warn.called

    @pytest.mark.slow
    def test_build_time_under_30s(self, tmp_path: pathlib.Path) -> None:
        import time
        from aio.commands.build import build_pipeline

        slides = tmp_path / "slides.md"
        slides.write_text(
            "---\ntitle: Perf Test\n---\n\n"
            "<!-- @image-prompt: slide 1 -->\n\n"
            "# S1\n\nBody.\n\n---\n\n"
            "<!-- @image-prompt: slide 2 -->\n\n"
            "# S2\n\nBody.",
            encoding="utf-8",
        )
        out = tmp_path / "out.html"
        start = time.perf_counter()
        with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
            build_pipeline(slides, output=out, enrich=True)
        elapsed = time.perf_counter() - start
        assert elapsed < 30.0, f"Enrich build took {elapsed:.1f}s, expected < 30s"
