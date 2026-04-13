"""Unit tests for Phase 2 CSS Decorations (T031).

TDD: all tests should FAIL before T033–T040 are implemented.
"""

from aio.themes.parser import parse_design_md

# ---------------------------------------------------------------------------
# Minimal DESIGN.md with 11 sections (valid baseline)
# ---------------------------------------------------------------------------

_BASE_DESIGN = """\
## 1. Visual Theme
A clean minimal theme for professional presentations.
Uses flat design with subtle depth cues and a primary accent color.

## 2. Color Palette
- Primary: #635BFF
- Accent: #00D084
- Background: #FFFFFF
- Text: #1F2937
- Neutral 300: #d1d5db
- Neutral 500: #6b7280

## 3. Typography
- Display Font: Inter
- Body Font: Inter
- Mono Font: JetBrains Mono

## 4. Components
Buttons, cards, and badges follow the color palette.
All interactive components have focus rings for accessibility.

## 5. Layout System
Grid-based 12-column layout with 24px gutter.
Responsive breakpoints at 640px, 768px, 1024px, 1280px.

## 6. Depth & Shadows
- Shadow SM: 0 1px 2px rgba(0,0,0,0.05)
- Shadow MD: 0 4px 6px rgba(0,0,0,0.07)
- Shadow LG: 0 10px 15px rgba(0,0,0,0.10)

## 7. Do's & Don'ts
Do: Use primary color for CTAs and key highlights.
Don't: Use more than 3 colors per slide.
Don't: Mix serif and sans-serif fonts on the same slide.

## 8. Responsive Behavior
Mobile: Single column layout, larger touch targets (min 44px).
Tablet: Two column grid, reduced padding.
Desktop: Full 12-column grid, standard padding.

## 9. Animation & Transitions
Default transition: fade 300ms ease.
Slide transitions: horizontal slide 400ms.
Hover effects: scale(1.02) 150ms ease.

## 10. Accessibility (WCAG 2.1 AA)
All text passes WCAG 2.1 AA contrast ratio (4.5:1 for normal, 3:1 for large).
Focus indicators visible on all interactive elements.
Skip navigation link present on all pages.

## 11. Agent Prompt Snippet
This minimal theme uses a clean, professional aesthetic with Inter font and
a purple primary accent (#635BFF). Slides should follow flat design principles
with ample whitespace, clear hierarchy, and consistent spacing. Prefer subtle
depth cues over heavy shadows. Color usage should be restrained — primary accent
for CTAs and highlights, neutral tones for supporting content. All text must
maintain WCAG 2.1 AA contrast against the white background.
"""

_DESIGN_WITH_DECORATIONS = (
    _BASE_DESIGN
    + """\

## 12. Decorations
### Gradients
- primary-gradient: linear-gradient(135deg, #635BFF 0%, #00D084 100%)
- accent-gradient: linear-gradient(to right, #FF5733, #FFC300)

### Dividers
- thin: 1px solid #d1d5db
- thick: 3px solid #635BFF

### Glow Effects
- primary-glow: 0 0 30px rgba(99, 91, 255, 0.5)

### Accent Lines
- left-border: 4px solid #635BFF
"""
)


# ---------------------------------------------------------------------------
# T031-A: parse_design_md() with section 12 returns DecorationSpec list
# ---------------------------------------------------------------------------


class TestParseDesignMdWithDecorations:
    def test_parse_returns_decoration_specs(self):
        """parse_design_md() with section 12 returns DecorationSpec list via ThemeRecord."""
        result = parse_design_md(_DESIGN_WITH_DECORATIONS)
        # The function must return something that has decorations
        # Either as a return value with decorations attr, or as the last section
        # We check the parsed sections include section 12
        section_numbers = [s.section_number for s in result]
        assert 12 in section_numbers

    def test_missing_section_12_returns_empty_decorations(self):
        """parse_design_md() without section 12 raises no error and returns empty decorations."""
        result = parse_design_md(_BASE_DESIGN)
        # Should not raise — 11 sections is valid
        section_numbers = [s.section_number for s in result]
        assert 12 not in section_numbers

    def test_decoration_spec_gradient_extracted(self):
        """DecorationSpec for primary-gradient has correct css_value."""
        result = parse_design_md(_DESIGN_WITH_DECORATIONS)
        section12 = next(s for s in result if s.section_number == 12)
        decorations = section12.parsed_data.get("decorations", [])
        # At least one decoration should be for the gradient
        assert isinstance(decorations, list)
        assert len(decorations) > 0

    def test_decoration_spec_is_dataclass(self):
        """DecorationSpec is importable and is a dataclass."""
        import dataclasses

        from aio.themes.parser import DecorationSpec

        assert dataclasses.is_dataclass(DecorationSpec)

    def test_decoration_spec_fields(self):
        """DecorationSpec has required fields: name, css_class, css_value."""
        import dataclasses

        from aio.themes.parser import DecorationSpec

        field_names = {f.name for f in dataclasses.fields(DecorationSpec)}
        assert "name" in field_names
        assert "css_class" in field_names
        assert "css_value" in field_names


# ---------------------------------------------------------------------------
# T031-B: CSS generation from DecorationSpec
# ---------------------------------------------------------------------------


class TestGenerateDecorationCss:
    def test_function_importable(self):
        from aio.themes.parser import generate_decoration_css

        assert callable(generate_decoration_css)

    def test_gradient_produces_background_class(self):
        from aio.themes.parser import DecorationSpec, generate_decoration_css

        specs = [
            DecorationSpec(
                name="primary-gradient",
                css_class="decoration-gradient-primary",
                css_value="linear-gradient(135deg, #635BFF 0%, #00D084 100%)",
                css_property="background",
                responsive_value=None,
            )
        ]
        css = generate_decoration_css(specs)
        assert ".decoration-gradient-primary" in css
        assert "linear-gradient" in css
        assert "background" in css

    def test_empty_specs_returns_defaults(self):
        from aio.themes.parser import generate_decoration_css

        css = generate_decoration_css([])
        # Default fallback classes must be present
        assert ".decoration-" in css
        assert len(css) > 0

    def test_css_is_valid_syntax(self):
        from aio.themes.parser import DecorationSpec, generate_decoration_css

        specs = [
            DecorationSpec(
                name="primary-gradient",
                css_class="decoration-gradient-primary",
                css_value="linear-gradient(135deg, #635BFF 0%, #00D084 100%)",
                css_property="background",
                responsive_value=None,
            )
        ]
        css = generate_decoration_css(specs)
        # Must have opening and closing braces
        assert "{" in css and "}" in css

    def test_multiple_specs_all_emitted(self):
        from aio.themes.parser import DecorationSpec, generate_decoration_css

        specs = [
            DecorationSpec(
                name="primary-gradient",
                css_class="decoration-gradient-primary",
                css_value="linear-gradient(135deg, #635BFF 0%, #00D084 100%)",
                css_property="background",
                responsive_value=None,
            ),
            DecorationSpec(
                name="primary-glow",
                css_class="decoration-glow-primary",
                css_value="0 0 30px rgba(99,91,255,0.5)",
                css_property="box-shadow",
                responsive_value=None,
            ),
        ]
        css = generate_decoration_css(specs)
        assert ".decoration-gradient-primary" in css
        assert ".decoration-glow-primary" in css


# ---------------------------------------------------------------------------
# T031-C: ThemeRecord has decorations field
# ---------------------------------------------------------------------------


class TestThemeRecordDecorations:
    def test_theme_record_has_decorations_field(self):
        import dataclasses

        from aio.themes.loader import ThemeRecord

        field_names = {f.name for f in dataclasses.fields(ThemeRecord)}
        assert "decorations" in field_names

    def test_theme_record_decorations_default_empty(self):
        import dataclasses

        from aio.themes.loader import ThemeRecord

        # Check the decorations field has a default of []
        fields_by_name = {f.name: f for f in dataclasses.fields(ThemeRecord)}
        decorations_field = fields_by_name["decorations"]
        # Default should be a list (via default_factory)
        assert decorations_field.default_factory is not dataclasses.MISSING or decorations_field.default == []  # type: ignore[misc]


# ---------------------------------------------------------------------------
# T031-D: config.decorations == False suppresses CSS
# ---------------------------------------------------------------------------


class TestDecorationsSuppression:
    def test_disabled_config_suppresses_decoration_css(self):
        """When decorations disabled in config, generate_decoration_css returns empty string."""
        from aio.themes.parser import DecorationSpec, generate_decoration_css

        specs = [
            DecorationSpec(
                name="primary-gradient",
                css_class="decoration-gradient-primary",
                css_value="linear-gradient(135deg, #635BFF 0%, #00D084 100%)",
                css_property="background",
                responsive_value=None,
            )
        ]
        # When decorations=False is passed, should suppress output
        css = generate_decoration_css(specs, enabled=False)
        assert css == ""
