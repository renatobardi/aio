# Implementation Plan: AIO Phase 2 — Visual Enrichment

**Branch**: `003-visual-enrichment` | **Date**: 2026-04-12 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/003-visual-enrichment/spec.md`

---

## Summary

Phase 2 (M2.5) completes the Visual Intelligence foundation by adding five incremental capabilities to the existing build pipeline:

1. **Inline metadata syntax** — `<!-- @key: value -->` HTML comment directives parsed from slide bodies, merged into `SlideAST.metadata`, and stripped from output HTML.
2. **Icon resolution** — `<!-- @icon: name -->` resolved from the extended bundled Lucide library (159 → 200+ icons) and inlined as styled `<svg>` elements; `aio icons list` command for discovery.
3. **Extended DataViz engine** — three new chart types (`DonutChart`, `SparklineChart`, `TimelineChart`) added to `charts.py` alongside the existing five; activated via `<!-- @chart: type -->` + `<!-- @data: ... -->`.
4. **CSS Decorations** — DESIGN.md section 12 parser generates `.decoration-{type}-{variant}` CSS classes appended to the document `<style>` block; slide `<section>` elements receive the class when `<!-- @decoration: ... -->` is present.
5. **Image Enrichment** — `aio build --enrich` triggers an optional Step 4.5 that generates contextual images via the Pollinations.ai free API, base64-encodes them, and inlines them into the output HTML, preserving the Art. II offline guarantee.

All changes are additive; no existing CLI interfaces or data model fields are removed.

---

## Technical Context

**Language/Version**: Python 3.12+ (primary runtime per Art. I)  
**Primary Dependencies**: mistune 3.0.2, Jinja2 3.1.2, typer 0.12.0, pyyaml 6.0.1, rich 13.7.0, watchdog, starlette, uvicorn — no new core deps; `pillow` (already in `[enrich]`) used for JPEG validation in `_enrich.py`  
**Storage**: Local filesystem (`~/.aio/logs/`, project `.aio/`)  
**Testing**: pytest, real temp directories for integration tests (no mocks for pipeline core)  
**Target Platform**: Python 3.12+ on macOS / Linux / Windows; all 4 distribution modes (Art. XII)  
**Project Type**: CLI tool + Python library  
**Performance Goals**: 5-slide build < 2 s (no `--enrich`); 5-slide `--enrich` build < 30 s; icon resolution < 1 ms per icon; chart generation < 10 ms per chart  
**Constraints**: Zero external URLs in output HTML (Art. II); no new core deps beyond stdlib + existing 10 (Art. VII); `urllib.request` for Pollinations HTTP calls  
**Scale/Scope**: 200+ icons in-memory; 8 chart types; up to 30 slides per deck typical

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design below.*

| Article | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| Art. I — Python 3.12+ | All new code targets 3.12+ | ✅ PASS | `match/case` used in chart dispatch; `A \| B` unions throughout |
| Art. II — Offline HTML | All SVGs, icons, images inlined at build time | ✅ PASS | `inline_assets()` step still fails on any external URL (exit 3); Pollinations images downloaded and base64-encoded before output |
| Art. III — Visual Intelligence | DataViz, icons, decorations are Phase 2 deliverables | ✅ PASS | This plan IS the Visual Intelligence milestone |
| Art. IV — Agent-agnostic prompts | No agent prompts changed | ✅ PASS | `ENRICH_PHASE.md` prompt stubs already planned for M2.5 per constitution |
| Art. V — DESIGN.md schema | Section 12 added additively | ✅ PASS | `extract.py` and parser updated together; `aio theme validate` updated to accept 11 or 12 sections |
| Art. VI — Free by default | Pollinations.ai free tier, no API key required | ✅ PASS | `urllib.request` only; optional key via env var `AIO_POLLINATIONS_KEY` |
| Art. VII — 10 core deps | No new core dependencies | ✅ PASS | `urllib.request` is stdlib; `pillow` already in `[enrich]`; no new packages |
| Art. VIII — Reveal.js 5.x | Reveal.js vendor not touched | ✅ PASS | |
| Art. IX — TDD | Tests written first, coverage must not regress | ✅ PASS | See test plan in quickstart.md |
| Art. X — 64+ themes | No theme registry changes | ✅ PASS | |
| Art. XI — Frozen agent prompts | No existing prompts modified | ✅ PASS | |
| Art. XII — 4 distribution modes | All new imports are absolute | ✅ PASS | No relative imports; no `sys.path` hacks |

**Security gates:**
- `yaml.safe_load()` exclusively — no new `yaml.load()` calls.
- SVG sanitization applied to all `render_icon()` output and chart SVG output via `CompositionEngine.sanitize_svg()`.
- Pollinations URL constructed via `urllib.parse.urlencode()` — no string interpolation of user input into URLs.
- `<!-- @image-prompt: -->` value is URL-encoded before API call; HTML-escaped before logging.

**Post-design re-check:** All gates remain green. No complexity violations introduced.

---

## Project Structure

### Documentation (this feature)

```text
specs/003-visual-enrichment/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli-contract.md  # Phase 1 output
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks — not created here)
```

### Source Code Changes (additive only)

```text
src/aio/
├── visuals/
│   ├── svg/
│   │   └── icons.py              # EXTEND: add ~41 icons; add list_icons(); add icon_tags dict
│   └── dataviz/
│       └── charts.py             # EXTEND: add DonutChart, SparklineChart, TimelineChart
├── commands/
│   ├── build.py                  # EXTEND: --enrich, --dry-run flags; wire Enrich step
│   └── icons.py                  # NEW: `aio icons list [--filter] [--count]`
├── composition/
│   ├── metadata.py               # EXTEND: SlideRenderContext + InlineMetadata + EnrichContext
│   └── engine.py                 # EXTEND: infer_layout(), apply_layout() (unchanged by Phase 2)
├── themes/
│   └── parser.py                 # EXTEND: parse_design_md() handles optional section 12 → DecorationSpec[]
└── _enrich.py                    # NEW: EnrichEngine, Pollinations client, prompt inference

tests/
├── unit/
│   ├── test_inline_metadata.py   # NEW
│   ├── test_icons.py             # NEW (extends existing if any)
│   ├── test_dataviz_phase2.py    # NEW
│   ├── test_decorations.py       # NEW
│   └── test_enrich.py            # NEW
├── integration/
│   ├── test_build_phase2.py      # NEW
│   └── test_build_enrich.py      # NEW (mocks Pollinations HTTP call)
└── fixtures/
    ├── slides_phase2.md          # NEW
    ├── mock_pollinations_response.jpg  # NEW
    └── expected_bar_chart.svg    # NEW (determinism check)
```

**Structure Decision**: Single-project layout (Option 1 from template). All Phase 2 additions live within the existing `src/aio/` tree. No new top-level packages.

---

## Complexity Tracking

No Constitution Check violations. No complexity justification required.
