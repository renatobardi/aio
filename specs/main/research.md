# Research: AIO — AI-Native Presentation Generator

**Phase 0 Output** | **Date**: 2026-04-11 | **Plan**: `specs/main/plan.md`

All technical choices were fully specified in the project constitution and user-provided
implementation plan. No NEEDS CLARIFICATION items were open at plan inception. This document
consolidates decisions and rationale for traceability.

---

## Decision Log

### Python Runtime

**Decision:** Python 3.12+ as primary target; tolerate 3.10+ for extended support
**Rationale:** Walrus operator `:=`, `A | B` type unions, `match/case`, `functools.cache`,
and `tomllib` (stdlib) are used without legacy shims. The offline-first distribution model
requires no runtime version negotiation.
**Alternatives considered:** Python 3.10 as minimum — rejected because it forfeits `match/case`
and `tomllib` without meaningful gain (no significant user base on 3.10-only systems for this
tool category).

---

### Markdown Parser

**Decision:** mistune 3.0+
**Rationale:** Pure Python, fast AST output, integrates with Pygments for syntax highlighting.
Supports custom renderers needed for layout-aware HTML generation.
**Alternatives considered:**
- `markdown-it-py` — comparable speed, but less extensible AST; Pygments integration less direct
- `commonmark` — spec-compliant but slower; no custom renderer hooks for slide-specific extensions
- `pandoc` (subprocess) — too heavy, breaks offline distribution requirement

---

### Template Engine

**Decision:** Jinja2 3.1+
**Rationale:** Battle-tested, secure by default (auto-escaping), extensible via custom filters.
The per-layout `.j2` template approach maps directly to the 16-layout architecture. Jinja2
supports `{% include %}` partials needed for composing slide templates.
**Alternatives considered:**
- Mako — faster but less safe by default (XSS risk in user-provided content)
- Chameleon — XML-based; incompatible with HTML-fragment slide templates

---

### HTTP Client

**Decision:** httpx 0.26+ (async-ready)
**Rationale:** Supports HTTP/2, async/await, retry logic out of the box. Required for Pollinations.ai
async image generation and `extract.py` web scraping. pytest-httpx mock support is first-class.
**Alternatives considered:**
- `requests` — sync only; incompatible with non-blocking image generation requirement
- `aiohttp` — async but more complex API; httpx has better ergonomics for the dual sync/async use case

---

### Reveal.js Version

**Decision:** Reveal.js 5.0.0+, pinned to < 6.0; vendored statically
**Rationale:** v5.x is the stable LTS-equivalent with UMD build support required for JS inlining.
v6.x introduces ES module-only builds (bare `import`/`export`) which cannot be safely inlined
without a bundler — contradicting Art. II (offline standalone HTML).
**Alternatives considered:**
- Impress.js — fewer layout options, no ecosystem
- Deck.js — unmaintained
- Custom slide renderer — significant scope; Reveal.js ecosystem (plugins, keyboard nav, PDF export)
  provides immediate value

---

### SVG Chart Rendering

**Decision:** Pure Python SVG generation (no D3, no canvas, no headless browser)
**Rationale:** External chart libraries (D3.js, Chart.js) require runtime JavaScript execution, which
contradicts the standalone HTML requirement unless rendered server-side. Headless Chrome/Playwright
adds heavy dependencies incompatible with Art. VII (minimal deps < 150 MB).
**Alternatives considered:**
- `matplotlib` — generates raster PNG by default; SVG output requires additional config; adds 40+ MB
- `plotly` — JavaScript-dependent; inline mode produces large bundles; not offline-safe in all modes
- `pygal` — pure Python SVG charts; viable alternative but less control over output; mistune decided over it
  in favor of full custom control needed for AIO's composition engine integration

---

### Image Generation (Free Tier)

**Decision:** Pollinations.ai as default provider (open API, no key)
**Rationale:** Satisfies Art. VI (free by default). REST API, supports text-to-image. httpx
async integration is straightforward. Base64 embed of downloaded images satisfies Art. II.
**Alternatives considered:**
- DALL-E — requires paid API key; violates Art. VI
- Stability AI — free tier limited; key required for consistent access
- Local Stable Diffusion — adds GPU/model weight dependencies far exceeding 250 MB limit

---

### CLI Framework

**Decision:** Typer 0.9+ with Click 8.1+ as companion
**Rationale:** Typer generates help text from Python type hints, reducing boilerplate. Click
provides lower-level primitives for edge cases. `cli.py` must NOT use `from __future__ import
annotations` (breaks Typer's runtime type introspection).
**Alternatives considered:**
- `argparse` (stdlib) — verbose; no auto-help from type hints; significantly more boilerplate
- `docopt` — string-based; no type safety; harder to test

---

### Distribution Strategy

**Decision:** 4 modes: zero-install, zipapp (.pyz), PyInstaller binary, pip
**Rationale:** Satisfies Art. XII (ubiquity). Each mode has a distinct user segment:
- `pip` → developers, CI/CD
- `.pyz` → no-install sharing, USB sticks
- binary → non-Python users (design teams, managers)
- zero-install → advanced users, air-gapped machines
**Alternatives considered:**
- Docker image — adds Docker dependency; too heavy for the target "works anywhere" promise
- Snap/AppImage — Linux-only; contradicts cross-platform requirement

---

### Testing Strategy

**Decision:** pytest + pytest-cov + pytest-asyncio + pytest-httpx; no `unittest.mock` for core pipeline
**Rationale:** Art. IX mandates TDD and 80%+ coverage. `unittest.mock` was explicitly banned for the
core pipeline after prior incidents (see constitution) where mocked tests passed while real integration
failed. pytest-httpx allows realistic HTTP mocking without monkeypatching.
**Alternatives considered:**
- `unittest` — compatible but inferior fixture system; no parametrize natively
- `hypothesis` — useful for property-based testing; deferred to post-M4 (out of scope for v0.1.0)

---

## All Clarifications Resolved

| Item | Status |
|------|--------|
| Python version minimum | ✅ 3.12+ primary, 3.10+ tolerated |
| Markdown parser choice | ✅ mistune 3.0+ |
| SVG chart approach | ✅ Pure Python, no canvas/D3 |
| Image generation free tier | ✅ Pollinations.ai |
| CLI framework | ✅ Typer + Click |
| Distribution modes | ✅ 4 modes defined |
| Test framework | ✅ pytest, no unittest.mock for pipeline |
| Reveal.js version | ✅ 5.x pinned, < 6.0 |
