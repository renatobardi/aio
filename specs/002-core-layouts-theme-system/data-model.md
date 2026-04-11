# Data Model: AIO Core Layouts & Theme System (M1)

**Phase 1 Output** | **Date**: 2026-04-11 | **Plan**: `specs/002-core-layouts-theme-system/plan.md`

---

## Core Entities

### LayoutTemplate

Represents a single discovered Jinja2 layout file. Instances are created at import time by `LayoutRegistry` by scanning the `src/aio/templates/layouts/` package directory via `importlib.resources`.

```python
@dataclass(frozen=True)
class LayoutTemplate:
    layout_id: str           # slug, e.g. "hero-title" (derived from filename stem)
    path: Path               # absolute path to the .j2 file
    supported_blocks: list[str]  # block names declared in the template
    description: str         # one-line docstring extracted from the first Jinja2 comment block
    is_fallback: bool        # True only for "content" — the catch-all layout
```

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `layout_id` | `str` | — | Non-empty; matches `^[a-z][a-z0-9-]*$`; unique within registry |
| `path` | `Path` | — | File must exist and have `.j2` extension |
| `supported_blocks` | `list[str]` | — | Non-empty; each block name matches `^[a-z_]+$` |
| `description` | `str` | `""` | May be empty if no docstring comment is present |
| `is_fallback` | `bool` | `False` | Exactly one `LayoutTemplate` in the registry must have `is_fallback=True` |

**Validation rules:**
- `layout_id` is derived from the `.j2` filename stem; derivation applies `re.sub(r'[^a-z0-9-]', '-', stem.lower())`.
- `supported_blocks` is populated by scanning the template source for `{% block <name> %}` declarations using a regex; this is a read-only introspection, not execution.
- Instantiation raises `LayoutDefinitionError` if `path` does not resolve or the file cannot be read.

---

### LayoutRegistry

A singleton that owns the complete map of `layout_id → LayoutTemplate`. Loaded once per process via `LayoutRegistry.get()` (lazy singleton pattern). Discovery uses `importlib.resources.files("aio.templates.layouts")` so the registry works correctly in all four distribution modes.

```python
@dataclass
class LayoutRegistry:
    _layouts: dict[str, LayoutTemplate]   # layout_id → LayoutTemplate
    _loaded: bool                          # True after first successful discovery

    @classmethod
    def get(cls) -> "LayoutRegistry": ...          # lazy singleton accessor
    def lookup(self, layout_id: str) -> LayoutTemplate: ...  # raises LayoutNotFoundError
    def all_ids(self) -> list[str]: ...            # sorted list of registered ids
    def fallback(self) -> LayoutTemplate: ...      # returns the is_fallback=True template
```

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `_layouts` | `dict[str, LayoutTemplate]` | `{}` | Populated at load time; never mutated after loading |
| `_loaded` | `bool` | `False` | Becomes `True` after `_discover()` completes without error |

**Validation rules:**
- `_discover()` raises `LayoutRegistryError` if zero `.j2` files are found in the templates directory.
- `_discover()` raises `LayoutRegistryError` if no template has `is_fallback=True` after scanning all files.
- `lookup(layout_id)` raises `LayoutNotFoundError` (subclass of `AIOError`) with the requested id in the message.
- The registry is considered immutable after loading; any mutation attempt after `_loaded=True` raises `RuntimeError`.

---

### ThemeRecord

One entry in `registry.json`. Represents all metadata needed to locate, validate, and apply a theme. Loaded by `themes/loader.py`.

```python
@dataclass
class ThemeRecord:
    id: str                      # slug, e.g. "minimal", "stripe-checkout"
    name: str                    # human display name, e.g. "Minimal"
    description: str             # one-sentence summary
    version: str                 # semver string, e.g. "1.0.0"
    author: str                  # name or handle
    source_url: str | None       # upstream URL; None for built-in themes
    categories: list[str]        # e.g. ["minimal", "dark", "business"]
    colors: dict[str, str]       # semantic token → hex, e.g. {"primary": "#0f172a"}
    typography: dict[str, str]   # e.g. {"heading_font": "Inter", "body_font": "Inter"}
    css_path: Path               # absolute path to theme.css
    layout_css_path: Path        # absolute path to layout.css
    design_md_path: Path | None  # absolute path to DESIGN.md; None if not present
    is_builtin: bool             # True for themes shipped with the package
```

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `id` | `str` | — | Matches `^[a-z][a-z0-9-]*$`; unique across registry |
| `name` | `str` | — | Non-empty; max 60 characters |
| `description` | `str` | `""` | Max 200 characters |
| `version` | `str` | `"1.0.0"` | Matches `^\d+\.\d+\.\d+$` |
| `author` | `str` | `"unknown"` | Max 80 characters |
| `source_url` | `str \| None` | `None` | If set, must match `^https?://` |
| `categories` | `list[str]` | `[]` | Each category matches `^[a-z][a-z0-9-]*$`; max 10 items |
| `colors` | `dict[str, str]` | — | Values match `^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$`; required keys: `primary`, `background`, `text` |
| `typography` | `dict[str, str]` | — | Required keys: `heading_font`, `body_font` |
| `css_path` | `Path` | — | File must exist at load time |
| `layout_css_path` | `Path` | — | File must exist at load time |
| `design_md_path` | `Path \| None` | `None` | If set, file must exist |
| `is_builtin` | `bool` | `False` | — |

**Validation rules:**
- Deserialised from registry.json via `ThemeRecord.from_dict(d: dict, base_dir: Path) -> ThemeRecord`; paths are resolved relative to `base_dir`.
- `colors` dict must contain at minimum `primary`, `background`, and `text` keys; additional tokens are permitted.
- Loading raises `ThemeValidationError` if required keys are absent or CSS files do not exist.

---

### SlideRenderContext

The complete context dict passed to `jinja2.Environment.get_template(layout_id + ".j2").render(...)`. Constructed by the COMPOSE step from a `SlideAST` + `ThemeRecord`.

```python
@dataclass
class SlideRenderContext:
    # Slide identity
    slide_index: int              # 0-based position in the deck
    slide_id: str                 # e.g. "slide-3" — used as HTML id attribute

    # Layout selection
    layout_id: str                # resolved layout, e.g. "hero-title"
    is_inferred: bool             # True if layout was auto-detected, False if explicit

    # Content
    title: str | None             # rendered HTML string for the slide title
    body_html: str                # rendered HTML string for the slide body
    speaker_notes: str | None     # raw Markdown string (rendered inside <aside class="notes">)

    # Structured content fields (per-layout; unused fields are None)
    stat_value: str | None        # e.g. "98%" — for stat-highlight
    stat_label: str | None        # e.g. "Uptime" — for stat-highlight
    quote_text: str | None        # for quote layout
    quote_attribution: str | None # for quote layout
    image_src: str | None         # base64 data URI — for split-image-text
    image_alt: str | None         # alt text — for split-image-text
    image_position: str           # "left" or "right" — for split-image-text

    # Theme variables (CSS custom properties to inject)
    theme_vars: dict[str, str]    # CSS property name → value

    # Reveal.js data attributes
    reveal_attrs: dict[str, str]  # e.g. {"data-transition": "fade"}

    # Metadata
    tags: list[str]               # from frontmatter `tags:` field
    duration_hint: int | None     # seconds, from frontmatter `duration:` field
```

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `slide_index` | `int` | — | ≥ 0 |
| `slide_id` | `str` | `f"slide-{slide_index}"` | Matches `^slide-\d+$` or custom string |
| `layout_id` | `str` | — | Must exist in `LayoutRegistry` |
| `is_inferred` | `bool` | `True` | — |
| `title` | `str \| None` | `None` | If set, valid HTML fragment; no `<script>` |
| `body_html` | `str` | `""` | Valid HTML fragment; no `<script>` tags |
| `stat_value` | `str \| None` | `None` | Required when `layout_id == "stat-highlight"` |
| `image_src` | `str \| None` | `None` | If set, must start with `data:image/` |
| `image_position` | `str` | `"right"` | Must be `"left"` or `"right"` |
| `theme_vars` | `dict[str, str]` | `{}` | Keys must start with `--`; values non-empty |
| `reveal_attrs` | `dict[str, str]` | `{}` | Keys must start with `data-` |
| `tags` | `list[str]` | `[]` | Each tag non-empty; max 40 characters |
| `duration_hint` | `int \| None` | `None` | If set, must be > 0 |

**Validation rules:**
- `body_html` and `title` are validated by `_validators.py`'s `sanitise_html_fragment()` which strips `<script>` tags and raises `RenderValidationError` on injection patterns.
- When `layout_id == "stat-highlight"`, `stat_value` must be non-None; construction raises `SlideContextError` otherwise.
- When `layout_id == "split-image-text"`, `image_src` must be non-None and must match `^data:image/`.

---

### ComposedSlide

Output of the COMPOSE step for a single slide. Holds the rendered HTML fragment and the context that produced it, enabling debug introspection and visual testing.

```python
@dataclass
class ComposedSlide:
    index: int                          # 0-based position in the deck
    layout_id: str                      # the layout actually used
    html_fragment: str                  # complete <section>...</section> string
    render_context: SlideRenderContext  # the context used to produce html_fragment
    warnings: list[str]                 # non-fatal issues detected during composition
```

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `index` | `int` | — | ≥ 0 |
| `layout_id` | `str` | — | Must exist in `LayoutRegistry` |
| `html_fragment` | `str` | — | Non-empty; must start with `<section` and end with `</section>` |
| `render_context` | `SlideRenderContext` | — | — |
| `warnings` | `list[str]` | `[]` | Each warning is a non-empty string |

**Validation rules:**
- `html_fragment` must begin with `<section` (whitespace-tolerant) and end with `</section>`; raises `RenderValidationError` otherwise.
- `html_fragment` must not contain any `<script` substring; raises `RenderValidationError` if found (constitution rule 7).
- `warnings` items are emitted to stderr via `_log.py` at `WARNING` level during COMPOSE step; they do not cause pipeline failure.

---

### BuildResult

Returned by the `build` command after the full PARSE → ANALYZE → COMPOSE → RENDER → INLINE pipeline completes. Written to stdout as JSON when `--json` flag is passed.

```python
@dataclass
class BuildResult:
    output_path: Path                    # absolute path to the produced .html file
    slide_count: int                     # total slides in the deck
    byte_size: int                       # size of the output file in bytes
    theme_id: str                        # id of the theme used
    elapsed_seconds: float               # wall-clock time for the full pipeline
    layout_histogram: dict[str, int]     # layout_id → count of slides using that layout
    warning_count: int                   # total warnings across all ComposedSlides
    enrich_used: bool                    # True if --enrich flag was active
```

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `output_path` | `Path` | — | Absolute; parent directory must exist |
| `slide_count` | `int` | — | ≥ 1 |
| `byte_size` | `int` | — | ≥ 1 |
| `theme_id` | `str` | — | Must exist in the active registry |
| `elapsed_seconds` | `float` | — | ≥ 0.0 |
| `layout_histogram` | `dict[str, int]` | `{}` | All values ≥ 0; sum of values == `slide_count` |
| `warning_count` | `int` | `0` | ≥ 0 |
| `enrich_used` | `bool` | `False` | — |

**Validation rules:**
- `BuildResult` is constructed only after the output file has been successfully written; `output_path.exists()` is asserted before construction.
- `byte_size` is populated via `output_path.stat().st_size` immediately after write.
- The `--json` serialiser uses `dataclasses.asdict()` with a custom `Path → str` converter; it never calls `json.dumps()` on a raw `Path` object.

---

### HotReloadEvent

Internal event passed via `asyncio.Queue` from the watchdog filesystem observer thread to the Starlette SSE endpoint handler coroutine. Not serialised to disk; exists only in memory during a `aio serve` session.

```python
@dataclass(frozen=True)
class HotReloadEvent:
    event_type: Literal["reload", "error"]  # "reload" triggers browser refresh
    message: str                             # human-readable description
    source_path: Path | None                 # file that triggered the event
    timestamp: float                         # time.monotonic() value at event creation
```

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `event_type` | `Literal["reload", "error"]` | — | Must be `"reload"` or `"error"` |
| `message` | `str` | — | Non-empty; max 500 characters |
| `source_path` | `Path \| None` | `None` | If set, must be absolute |
| `timestamp` | `float` | — | `time.monotonic()` at creation; ≥ 0.0 |

**Validation rules:**
- `HotReloadEvent` is `frozen=True`; any mutation attempt raises `FrozenInstanceError`.
- The SSE endpoint serialises the event as `data: {"type": "<event_type>", "message": "<message>"}\n\n` using `json.dumps`; `source_path` is omitted from the wire format.
- Error events (`event_type="error"`) are created if the build subprocess exits non-zero; `message` contains the last line of stderr, truncated to 500 characters.

---

### DesignSection

One parsed section from a `DESIGN.md` file. Produced by `themes/validator.py`'s `parse_design_md(text: str) -> list[DesignSection]`. There must be exactly 11 `DesignSection` instances for a DESIGN.md to pass validation.

```python
@dataclass
class DesignSection:
    section_number: int       # 1–11, from the "## N. Heading" prefix
    heading: str              # heading text without the "N." prefix, stripped
    raw_content: str          # full body text of the section (Markdown, not rendered)
    parsed_data: dict         # structured data extracted from fenced ```yaml blocks
    char_count: int           # len(raw_content) — used to enforce minimum content requirements
```

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `section_number` | `int` | — | 1 ≤ value ≤ 11; must be unique within a parsed document |
| `heading` | `str` | — | Non-empty after strip; max 80 characters |
| `raw_content` | `str` | — | Non-empty; `char_count` ≥ 50 |
| `parsed_data` | `dict` | `{}` | Populated only when a ` ```yaml ` block is present; uses `yaml.safe_load()` exclusively |
| `char_count` | `int` | `len(raw_content)` | Derived field; always equals `len(raw_content)` |

**Validation rules:**
- `parse_design_md()` raises `DesignSectionParseError` if fewer than 11 sections are found; the error message lists the missing section numbers.
- `parse_design_md()` raises `DesignSectionParseError` if section numbers are non-contiguous.
- Section 2 (Color Palette) requires `parsed_data` to be non-empty and contain at least one hex value matching `^#[0-9a-fA-F]{3,6}$`; raises `DesignSectionValidationError` if absent.
- Section 11 (Agent Prompt Snippet) requires `char_count` ≥ 200; raises `DesignSectionValidationError` if shorter.
- `parsed_data` is always produced by `yaml.safe_load()`; if the fenced block cannot be parsed, `parsed_data` is set to `{"_parse_error": "<exception message>"}` and a warning is emitted rather than raising.
