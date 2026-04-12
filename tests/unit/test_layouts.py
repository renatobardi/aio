"""Unit tests for the 8 M1 layout templates (T013)."""

from __future__ import annotations

import time

import pytest

from aio._utils import build_jinja_env

LAYOUTS = [
    "hero-title",
    "stat-highlight",
    "split-image-text",
    "content-with-icons",
    "comparison-2col",
    "quote",
    "key-takeaways",
    "closing",
]

# Minimal context sufficient to render each layout without errors
_BASE_CTX: dict = dict(
    slide_index=0,
    slide_id="slide-0",
    is_inferred=False,
    title="Test Title",
    body_html="<p>Body content</p>",
    speaker_notes=None,
    stat_value="87%",
    stat_label="Accuracy",
    stat_description="Across all tests",
    quote_text="Innovation is about saying no.",
    quote_attribution="Steve Jobs",
    image_src=None,
    image_alt="Test image",
    image_position="right",
    cta_text="Get started",
    left_title="Option A",
    left_content="Feature 1, Feature 2",
    right_title="Option B",
    right_content="Feature 1, Feature 2, Feature 3",
    theme_vars={},
    reveal_attrs={},
    tags=[],
    duration_hint=None,
)


@pytest.fixture(scope="module")
def jinja_env():
    return build_jinja_env("aio.layouts")


@pytest.mark.parametrize("layout_id", LAYOUTS)
def test_layout_renders_section(jinja_env, layout_id: str) -> None:
    """Each layout must produce a <section> wrapper with data-layout attribute."""
    template_name = layout_id.replace("-", "_") + ".j2"
    tmpl = jinja_env.get_template(template_name)
    ctx = {**_BASE_CTX, "layout_id": layout_id}
    html = tmpl.render(**ctx)

    assert html.strip().startswith("<section"), f"{layout_id}: output must start with <section"
    assert html.strip().endswith("</section>"), f"{layout_id}: output must end with </section>"
    assert f'data-layout="{layout_id}"' in html, f"{layout_id}: must have data-layout attribute"


@pytest.mark.parametrize("layout_id", LAYOUTS)
def test_layout_no_script_tag(jinja_env, layout_id: str) -> None:
    """No <script> tag may appear in any layout output (Constitution Rule 7)."""
    template_name = layout_id.replace("-", "_") + ".j2"
    tmpl = jinja_env.get_template(template_name)
    ctx = {**_BASE_CTX, "layout_id": layout_id}
    html = tmpl.render(**ctx)

    assert "<script" not in html.lower(), f"{layout_id}: must not contain <script tags"


@pytest.mark.parametrize("layout_id", LAYOUTS)
def test_layout_has_layout_class(jinja_env, layout_id: str) -> None:
    """Each layout section must carry the .layout-{name} CSS class."""
    template_name = layout_id.replace("-", "_") + ".j2"
    tmpl = jinja_env.get_template(template_name)
    ctx = {**_BASE_CTX, "layout_id": layout_id}
    html = tmpl.render(**ctx)

    assert f"layout-{layout_id}" in html, f"{layout_id}: must contain class 'layout-{layout_id}'"


class TestLayoutRenderPerformance:
    """SC-200 gate: each layout must render in under 10ms (warm Jinja2 env)."""

    @pytest.mark.parametrize("layout_id", LAYOUTS)
    def test_render_under_10ms(self, jinja_env, layout_id: str) -> None:
        template_name = layout_id.replace("-", "_") + ".j2"
        tmpl = jinja_env.get_template(template_name)
        ctx = {**_BASE_CTX, "layout_id": layout_id}

        # Warm up
        tmpl.render(**ctx)

        start = time.perf_counter()
        tmpl.render(**ctx)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 10, f"{layout_id}: render took {elapsed_ms:.2f}ms, must be < 10ms (SC-200)"
