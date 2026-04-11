# Research: AIO Core Layouts & Theme System (M1)

**Phase 0 Output** | **Date**: 2026-04-11 | **Plan**: `specs/002-core-layouts-theme-system/plan.md`

This document inherits all project-level research recorded in `specs/main/research.md` (M0). Only decisions that are new or that override M0 choices are recorded here.

---

## Decision Log

### 1. Jinja2 Layout Inheritance Strategy

**Decision:** `base.j2` with `{% extends %}` and named blocks (`{% block slide_content %}`, `{% block slide_attrs %}`, `{% block slide_class %}`).

**Rationale:**
Flat `{% include %}` templates require each layout to re-declare the `<section>` wrapper, `data-*` attributes, speaker-notes block, and the JS hook for Reveal.js transitions. That is six to eight lines of boilerplate that must stay identical across all eight layouts. Any divergence silently breaks Reveal.js slide detection (it requires a clean `<section>` hierarchy). The `{% extends %}` model centralises that boilerplate in `base.j2`, enforces the structure contract at render time (Jinja2 raises `UndefinedError` if a required block is missing), and keeps individual layout files to only the markup that is genuinely different. `base.j2` also becomes the single place to escape `</script>` → `<\/script>` inside any inline JS block — satisfying the constitution constraint once, not eight times.

`{% include %}` was considered for composable sub-templates (e.g. a shared `_icon_row.j2`). That pattern is kept as a secondary pattern *within* layout templates for repeating micro-components, but not as the primary inheritance mechanism.

**Alternatives considered:**
- **Flat templates with a render helper function** — avoids Jinja2 inheritance entirely; the Python side assembles fragments. Rejected: moves structural logic out of templates and into Python, making it harder for theme authors to reason about what the HTML will look like.
- **Jinja2 macros in a shared `_macros.j2`** — good for icon rows and stat cards, kept as a complement but not a replacement for `extends`.

---

### 2. CSS Custom Properties Architecture

**Decision:** A three-layer custom-property hierarchy declared in `theme.css`:

1. **Primitive tokens** — raw values with no semantic meaning: `--color-neutral-900: #0f172a;`
2. **Semantic tokens** — role-based aliases that reference primitives: `--color-bg: var(--color-neutral-900);`
3. **Component tokens** — scoped to slide layouts: `--slide-hero-title-size: 4rem;`

All layout CSS uses only semantic and component tokens. No hardcoded hex values or pixel sizes appear in layout templates or `layout.css`.

**Rationale:**
AIO must support 64+ imported themes whose source CSS uses arbitrary hex codes. During import the extraction step maps those hex codes to primitive tokens; the semantic layer provides a stable interface that layouts can rely on regardless of which theme is active. This means `split-image-text.j2` can reference `var(--color-text)` and work correctly with every imported theme without modification. Without this separation, each layout would need theme-specific overrides, making the template count explode to `8 layouts × 64 themes`.

The three-layer approach is the same pattern used by Radix UI and Primer Design System and is well-proven for CLI-distributed component libraries where the consumer cannot modify the host CSS.

**Alternatives considered:**
- **Single flat token layer** — simpler but forces layouts to know about primitive values, breaking the abstraction.
- **SCSS variables** — not viable; AIO's constitution forbids build-time CSS tooling dependencies; output must be pure browser-ready CSS from a stdlib-only build pipeline.
- **Inline style attributes on `<section>` elements** — viable for a single theme but makes overriding impossible and defeats Reveal.js's own CSS cascade.

---

### 3. DESIGN.md Section Parser

**Decision:** A single compiled regular expression with `re.MULTILINE | re.DOTALL` that splits on heading anchors, followed by per-section structured parsing using `yaml.safe_load()` for fenced YAML blocks and plain text extraction for prose sections.

The top-level splitter pattern:

```python
SECTION_RE = re.compile(
    r'^##\s+(?P<number>\d+)\.\s+(?P<heading>[^\n]+)\n(?P<body>.*?)(?=^##\s+\d+\.|^#\s+|\Z)',
    re.MULTILINE | re.DOTALL,
)
```

Any fenced code block tagged ` ```yaml ` inside the section body is extracted with a second pass and parsed with `yaml.safe_load()`. The remainder is stored as `raw_content`.

**Rationale:**
DESIGN.md is a human-authored Markdown document. A full Markdown AST parser (mistune, which is already a dependency) was considered but rejected for the parser role: mistune produces a tree optimised for rendering, not for extracting named sections, and traversing that tree for section boundaries requires more code than the regex approach with no accuracy benefit. The constitution already mandates `yaml.safe_load()` for all YAML parsing; the hybrid regex + YAML approach keeps that guarantee while handling the two content types that actually appear in DESIGN.md (structured data in fenced blocks, prose in the heading body).

The compiled regex is stored as a module-level constant so it is not recompiled on every parse call. `re.DOTALL` is required because section bodies span multiple lines; `re.MULTILINE` is required so `^` anchors match at line starts rather than only the string start.

**Alternatives considered:**
- **mistune full parse** — accurate AST but the traversal code is longer than the regex and mistune's heading nodes do not preserve inter-heading body text as a single string.
- **Split on `\n## `** — simple string split works for flat documents but fails when a theme DESIGN.md has nested `###` headings inside a section body (which several awesome-design-md sources do).
- **Third-party Markdown section extractor (markdown-it-py, marko)** — adds a dependency that the constitution's minimal-dependency rule does not permit.

---

### 4. Image Inlining Strategy

**Decision:** Python stdlib `base64` + `mimetypes` only. No Pillow dependency for the core pipeline.

Algorithm:
1. Resolve the image path relative to the source Markdown file.
2. Detect MIME type via `mimetypes.guess_type(path)`, falling back to `image/png`.
3. Read bytes, encode with `base64.b64encode(data).decode()`.
4. Produce `data:{mime};base64,{encoded}` and substitute into the `<img src>` or CSS `background-image` attribute before Step 4 (INLINE).

For the `split-image-text` layout, the image is inlined as a CSS `background-image` on the `.slide-image-panel` element, not as an `<img>` tag, so it participates in the CSS sizing system rather than requiring explicit `width`/`height` management.

**Rationale:**
The constitution specifies that core dependencies total < 150 MB. Inlining requires only reading bytes and base64-encoding them — no pixel manipulation, resize, or format conversion is needed. Pillow's only advantage here would be format normalisation (e.g. converting a TIFF to PNG before inlining). The `[enrich]` extra already gates Pillow for image generation; the constitution deliberately separates core from enrich. Format conversion, if needed, is deferred to the `[enrich]` pipeline.

`mimetypes.guess_type` is stdlib and covers all common web image formats (PNG, JPEG, GIF, SVG, WebP). SVG is inlined as-is (not base64) when the MIME is `image/svg+xml`, since embedding the raw SVG text is smaller; the SVG sanitiser from `_validators.py` (which strips `<script>` tags — constitution rule 7) runs before inlining.

**Alternatives considered:**
- **Pillow for all images** — rejected; over-engineered for a read-and-encode operation; violates the < 150 MB core budget.
- **`pathlib.Path.read_bytes()` + hardcoded MIME map** — simpler but `mimetypes` is already stdlib and handles edge cases (`.jpg` vs `.jpeg`, `.jfif`) automatically.
- **Keep image as external `<img src="file://...">` path** — violates constitution Art. II (no external URLs in output HTML).

---

### 5. Layout Inference Algorithm

**Decision:** A deterministic priority chain evaluated in this order:

```
1. closing          — slide index == last slide  OR  title contains "thank you", "questions",
                      "the end", or "contact" (case-insensitive)
2. hero-title       — slide index == 0  OR  title present + no body blocks
3. stat-highlight   — body contains exactly one token matching ^\d[\d,.]*[%x+]?$ as a standalone paragraph
4. quote            — body contains a blockquote (> prefix) as the primary block
5. split-image-text — body contains an image node (![...]) as a top-level block
6. comparison-2col  — body contains exactly two top-level ### headings of roughly equal weight
7. key-takeaways    — body contains an unordered list with 3–7 items and no other primary block types
8. content-with-icons — body unordered list where ≥50% of items begin with a recognised icon keyword
9. content          — fallback
```

`frontmatter layout: <id>` always overrides inference entirely. `@layout: auto` or missing layout tag triggers the chain.

**Rationale:**
The priority order is designed so that the most semantically unambiguous signals fire first. `closing` and `hero-title` are positional — they depend on slide index, which is a stronger signal than content heuristics. `stat-highlight` fires before `quote` because a big number is a very specific pattern unlikely to appear in a quote. `split-image-text` fires before list-based layouts because images are structurally unambiguous in the AST. The `frontmatter override` escape hatch is essential: inference will inevitably be wrong for edge cases, and the constitution's philosophy demands that a user can always force a layout without fighting the algorithm.

**Alternatives considered:**
- **ML classifier** — unacceptable dependency weight; introduces non-determinism; violates constitution's predictability requirement.
- **Scoring system** (accumulate votes from multiple signals) — more robust in theory but produces surprising results when two signals tie; the priority chain is easier to document and test.
- **Always require explicit `layout:` frontmatter** — too much friction for the core value proposition.

---

### 6. awesome-design-md Import Architecture

**Decision:** `git clone --depth 1 <url> <tempdir>` into a system temp directory, walk the clone for `DESIGN.md` files, parse each, validate the 11-section schema, emit a `ThemeRecord` per valid file, write to `src/aio/themes/registry.json`. On subsequent runs, if the clone directory already exists, run `git pull --ff-only` instead of a fresh clone. The import script (`scripts/import-awesome-designs.py`) is a standalone CLI, not part of the `aio` runtime.

Theme discovery heuristic inside the repo: any directory containing both a `DESIGN.md` and at least one `.css` file is treated as a theme candidate. The directory name becomes the theme `id` after slug-normalisation (`re.sub(r'[^a-z0-9-]', '-', name.lower())`).

**Rationale:**
`--depth 1` skips full history (the awesome-design-md repo has hundreds of commits of no interest to AIO); the shallow clone is roughly 10× faster and 5–10× smaller. The import script is decoupled from the runtime so that `aio` itself has no git dependency at runtime — the constitution's < 150 MB core budget and the "no hidden network calls" principle both require this separation. The incremental `git pull --ff-only` path avoids re-downloading on CI runs where the cache persists.

The 11-section validator runs during import, not at runtime, so invalid upstream DESIGN.md files are caught early and logged to stderr without crashing the import of the remaining themes. The import script exits with code 1 if zero themes were successfully imported, and with code 0 if some themes were skipped (partial success is acceptable; the registry always reflects what was actually validated).

**Alternatives considered:**
- **GitHub API + raw file downloads** — avoids a git dependency but rate-limits at 60 req/hr unauthenticated; not viable for 64 themes × multiple files each.
- **Vendoring the DESIGN.md files directly into the repo** — simplest but makes upstream updates a manual PR; the import script model keeps the update path scripted.
- **`pip install gitpython`** — GitPython is a pure-Python git interface but adds a runtime dependency and is slower than shelling out to `git` for the two operations needed here.

---

### 7. SSE Hot Reload Implementation

**Decision:** Starlette `EventSourceResponse` with a per-connection `asyncio.Queue`, fed by a single shared `watchdog.observers.Observer` running in a background thread. The observer posts reload events onto a module-level `asyncio.Queue` using `loop.call_soon_threadsafe(queue.put_nowait, event)`. Each SSE connection drains from its own per-connection copy of the queue (the shared queue fans out via a simple broadcast list).

`aio serve` binds to `127.0.0.1` by default; `--host 0.0.0.0` is available but documented as a development-only override flag.

**Rationale:**
Starlette is the mandated web framework. `EventSourceResponse` is available in `starlette.responses` and implements the SSE wire protocol correctly, handling `Last-Event-ID` reconnection and `Connection: keep-alive` headers. The alternative — WebSockets — requires a JS client that handles the upgrade handshake; SSE needs only `new EventSource('/__sse__')` in the injected JS snippet, which is smaller and more compatible with the no-external-URL constraint (no Socket.IO CDN).

watchdog is a Python filesystem notification library that wraps OS-native APIs (FSEvents on macOS, inotify on Linux, ReadDirectoryChangesW on Windows). It runs in a daemon thread so it does not block the Starlette event loop. The thread-safe queue bridge (`call_soon_threadsafe`) is the standard pattern for crossing the thread/async boundary in asyncio.

The 127.0.0.1 default satisfies the principle of least privilege: hot reload is a development feature and should not be accidentally exposed on a shared network interface.

**Alternatives considered:**
- **WebSockets** — more capable but heavier client code; SSE is sufficient for one-way server-to-browser notification.
- **Polling (`setInterval` in the injected JS)** — no server-side dependency on watchdog, but creates unnecessary HTTP traffic and adds ~1s latency vs the sub-100ms watchdog path on most filesystems.
- **`asyncio` `loop.run_in_executor` for file watching** — `watchdog` provides debouncing and recursive directory watching out of the box; reimplementing that with `os.stat` polling in an executor is more code and less reliable.

---

### 8. Fuzzy Theme Search

**Decision:** `difflib.SequenceMatcher(None, query, candidate).ratio()` with a minimum threshold of **0.6**. Search is applied to the `id`, `name`, and each string in `categories` for each `ThemeRecord`. The candidate field that produces the highest ratio is used for ranking. Results are returned sorted by descending ratio; the top 10 are shown by default.

Before matching, both query and candidate strings are lowercased and stripped of punctuation (`re.sub(r'[^a-z0-9 ]', ' ', s)`). The `id` field match is boosted by +0.1 (capped at 1.0) because users are more likely to remember a theme id from a previous `aio theme list` invocation.

**Rationale:**
`difflib` is stdlib. The constitution's dependency rules prohibit adding `rapidfuzz`, `thefuzz`, or `fuzzywuzzy` for what is a secondary UX feature. `SequenceMatcher` with ratio ≥ 0.6 handles the most common user mistakes: transpositions (`mnimal` → `minimal`), truncation (`min` → `minimal`), and hyphen/space variants (`key takeaways` → `key-takeaways`). Threshold 0.6 was chosen because at 0.5 too many false positives appear for short queries, and at 0.7 legitimate partial matches are missed.

**Alternatives considered:**
- **`rapidfuzz.fuzz.WRatio`** — best-in-class accuracy and ~40× faster than SequenceMatcher, but adds a compiled C extension dependency (~2 MB). Not justified for a UX feature that runs at human-interaction speed.
- **Substring containment only (`query in candidate`)** — zero false positives but misses any typo; unacceptable for a theme search feature.
- **Levenshtein edit distance** — equivalent accuracy to SequenceMatcher ratio for short strings; stdlib does not include it so it would require the same external dependency debate as rapidfuzz.
