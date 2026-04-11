<!--
SYNC IMPACT REPORT
==================
Version change: (template) → 1.0.0
Constitution filled from scratch — no prior version.

Modified principles: N/A (initial ratification)

Added sections:
  - Core Principles (12 Articles)
  - Technical Constraints
  - Implementation Milestones
  - Amendment Process
  - Governance

Removed sections: N/A

Templates requiring updates:
  ✅ .specify/memory/constitution.md (this file)
  ✅ .specify/templates/plan-template.md — Constitution Check gates already use
       "[Gates determined based on constitution file]"; no structural update
       needed, but plan instances MUST reference the 12 articles below
  ✅ .specify/templates/spec-template.md — generic; no constitution-specific
       tokens; no update needed
  ✅ .specify/templates/tasks-template.md — generic; no update needed

Follow-up TODOs:
  - None; all placeholders resolved.
-->

# AIO Constitution

## Core Principles

### I. Python 3.12+ As Platform Language

AIO MUST be developed targeting Python 3.12+ as the primary runtime. No backward
compatibility with Python < 3.10 is required.

- Use walrus `:=`, type unions `A | B`, `match/case`, `functools.cache`,
  `tomllib` (built-in), and modern async/await patterns.
- `typing.Union[A, B]` MUST NOT be used — replace with `A | B` throughout.
- Type hints, `@dataclass`, `TypedDict`, and `Protocol` are first-class.
- Add `from __future__ import annotations` where appropriate **except** in files
  that use Typer at runtime (`cli.py`, `serve.py`).

**Rationale**: Modern Python syntax enables cleaner, more expressive code without
legacy shims. Targeting 3.12+ removes the overhead of maintaining compatibility
layers that add complexity with no user benefit.

---

### II. 100% Standalone Offline HTML Output (Portability Law)

Every generated presentation MUST be a single `.html` file that is entirely
self-contained. Zero external runtime dependencies are permitted.

- All assets (CSS, JS, SVG, woff2 fonts, base64 images) MUST be inlined inside
  `<style>` or `<script>` tags.
- No `<link href="https://...">` and no `<script src="https://...">` are allowed
  in any generated output.
- Reveal.js vendor code is static and updated manually — never fetched at runtime.
- Images generated via `--enrich` (Pollinations.ai) MUST be downloaded during
  build and embedded as base64 or inline SVG.
- The `build` command MUST fail if it detects any external URL reference (except
  `data:` URIs) in the output HTML.

**Rationale**: A presentation that stops working when internet is unavailable is
not a deliverable. Offline-first is the product guarantee.

---

### III. Visual Intelligence As Core Differentiator

Intelligent visual composition, dynamic layouts, SVG composites, and data
visualizations are NOT optional features — they ARE the product. Every
architectural decision MUST prioritize visual expressiveness.

- The **Composition Engine** (`src/aio/composition/`) is foundational, not an
  add-on. It orchestrates layouts, SVG, and data viz from the parsing step.
- **16+ layouts** are planned from M0 onward: Title, Content, Two-Column,
  Three-Column, Full-Image, Code, Quote, Timeline, Comparison, Gallery, Data,
  Icon Grid, Narrative, Diagram, Custom, Interactive.
- The **SVG Composites engine** (`src/aio/visuals/svg/`) renders complex static
  illustrations; the **DataViz Engine** (`src/aio/visuals/dataviz/`) converts
  CSV/JSON/inline data → SVG charts (bar, line, pie, scatter, heatmap).
- The icon library (~200 Lucide icons) is vendored and CSS-customizable.
- Every generated slide MUST pass through `Composition.infer_layout()`. No slide
  leaves the renderer without layout inference.

**Rationale**: The differentiation vs NotebookLM, Canva, and Figma is visual
quality + automation speed. Treating visuals as an afterthought would eliminate
the reason to exist.

---

### IV. Agent-Agnostic Multimodal Prompting

AIO MUST support 8 AI agents natively, each with a dedicated prompt template. No
agent is a second-class citizen. Intelligence lives in the prompts, not in the
orchestrator.

Supported agents: Claude (default), Gemini, Copilot, Windsurf, Devin, ChatGPT,
Cursor, Generic REST API.

- `src/aio/agent_commands/` MUST contain one directory per agent (`claude/`,
  `gemini/`, `copilot/`, `windsurf/`, `devin/`, `chatgpt/`, `cursor/`, `generic/`).
- Each agent directory MUST contain: `SYSTEM.md`, `INIT_PHASE.md`,
  `COMPOSITION_PHASE.md`, `ENRICH_PHASE.md`, `REFINEMENT_PHASE.md`.
- Prompts are vendored at release time — never fetched dynamically.
- The CLI `--agent` flag selects the template; default is `claude`.
- Each agent MUST pass a smoke test: generate a 5-slide presentation validating
  HTML structure + visual composition.

**Rationale**: Agent-specific prompts unlock the full capability of each platform.
A single generic prompt degrades quality across the board.

---

### V. DESIGN.md Dual-Purpose: Human + Machine

Every theme MUST contain a `DESIGN.md` file that serves simultaneously as human
documentation and as a parsing-ready machine specification for `extract.py` and
prompt templates.

The following 11 sections are MANDATORY in every `DESIGN.md`:

1. Visual Theme
2. Color Palette (hex values, roles, contrast ratios)
3. Typography (fonts, sizes, line-heights, weights)
4. Components (buttons, badges, cards, callouts, code blocks)
5. Layout System (grid, spacing scale, breakpoints)
6. Depth & Shadows (elevation levels 0–4, shadow definitions)
7. Do's & Don'ts
8. Responsive Behavior
9. Animation & Transitions
10. Accessibility (WCAG 2.1 AA compliance, contrast guarantees)
11. Agent Prompt Snippet (~200 words, executable by an AI agent)

- Sections MUST use standard Markdown (headers, lists, code blocks, tables).
- No format changes are permitted without a Constitution Amendment and simultaneous
  update to `extract.py`.
- Every theme is validated against a JSON schema at build time.

**Rationale**: A spec that only a human can read forces AI agents to guess at
visual intent. Machine-parseable structure makes every theme a first-class prompt
asset.

---

### VI. Free by Default (Economic Accessibility Law)

Every "premium" capability (image generation, visual enrichment) MUST work free
of charge by default via Pollinations.ai (open API, no key required).

- `--enrich` uses Pollinations.ai as the default provider — no API key is ever
  required to get full functionality.
- Paid providers (DALL-E, Midjourney, Stable Diffusion) are supported via optional
  manual configuration.
- No core feature requires a paid subscription.
- If all providers fail, the build MUST fall back to SVG placeholders and complete
  successfully.
- Logs MUST indicate which provider is in use.

**Rationale**: A tool that gates visual richness behind a paid API is not truly
portable. The product promise is zero-cost, zero-friction quality.

---

### VII. Minimal but Modern Dependency Stack

AIO MUST use exactly 9 core runtime dependencies (without `[extract]`/`[enrich]`
extras). All must be actively maintained and < 2 MB each.

**Core (always)**: `typer >= 0.9`, `jinja2 >= 3.1`, `mistune >= 3.0`,
`pyyaml >= 6.0`, `pygments >= 2.15`, `watchdog >= 3.0`, `httpx >= 0.25`,
`click >= 8.1`, `rich >= 13.0`.

**Optional `[enrich]`**: `pillow >= 10.0`, `beautifulsoup4 >= 4.12`,
`lxml >= 4.9`, `cssutils >= 2.7`.

**Permanently forbidden**: Django, numpy, pandas, tensorflow (too heavy); any web
framework other than minimal ASGI for `serve.py`; ORMs; GraphQL.

- `pip install -e .` MUST produce an environment < 150 MB.
- `pip install -e ".[enrich]"` MUST produce an environment < 250 MB.

**Rationale**: A bloated dependency tree conflicts with the offline-first, zero-
install, and portability guarantees. Every added dependency is a threat to the
distribution model.

---

### VIII. Reveal.js 5.x Pinned (IMMUTABLE)

Reveal.js MUST be pinned to `5.0.0 <= version < 6.0`. Upgrade to v6.x is
permanently prohibited without a formal Constitution Amendment.

- Vendor code lives in `src/aio/vendor/revealjs/dist/` as static files; never
  fetched via npm.
- UMD builds only (required for JS inlining).
- Any new Reveal.js file MUST be checked for bare `import`/`export` before
  vendoring.
- All inlined JS MUST escape `</script>` → `<\/script>`.
- The build MUST fail if it detects Reveal.js v6+ or unescaped bare modules.

**Rationale**: Reveal.js v6 introduces breaking API changes. The effort to migrate
outweighs any benefit, and stability is more valuable than novelty for a tool
whose primary asset is its output HTML.

---

### IX. Test-First, 80% Coverage Mandatory

Every new feature MUST have tests written BEFORE implementation (TDD). Coverage
target: 80% line coverage + 75% branch coverage.

**Test structure**:
- `tests/unit/` — isolated functions, I/O mocks (~60% of total tests)
- `tests/integration/` — full pipeline (parse → build → output) using real temp
  directories (~20%)
- `tests/visual/` — visual regression (HTML snapshots, SVG validation) (~10%)
- `tests/fixtures/` — sample slides, themes, expected outputs

- `unittest.mock` MUST NOT be used for the core pipeline (init, build, compose,
  enrich) — use real integration instead.
- Agent command tests MUST use mocks (no live API calls in CI).
- `pytest --cov=src/aio --cov-report=term-missing` MUST report 80%+ or CI fails.

**Rationale**: Mocked pipeline tests have historically masked production failures.
Real integration tests against the actual I/O pipeline catch regressions that
mocks miss.

---

### X. Theme Library: 64+ Themes (Visual Diversity Law)

AIO MUST ship with 64+ themes sourced from `awesome-design-md`, each fully
functional, tested, and validated against the DESIGN.md schema.

- Global registry: `src/aio/themes/registry.json` — full metadata.
- Per-project registry: `.aio/themes/registry.json` — selected theme only (never
  copy the global registry into a project).
- Each theme lives in its own directory: `src/aio/themes/{id}/` containing
  `DESIGN.md`, `theme.css`, `layout.css`, `meta.json`.
- `scripts/import-awesome-designs.py` synchronizes themes nightly via GitHub
  Actions.
- The fallback theme (`minimal`) MUST always be available, including offline.

**Rationale**: A tool positioned on visual quality must back the claim with variety.
64+ themes demonstrates the engine is genuinely flexible, not a one-trick aesthetic.

---

### XI. Agent Commands Versioned and Frozen at Release

Agent prompt files (system, init, compose, enrich, refine) MUST be versioned and
frozen in each release. They are never fetched live; never updated via API.

- Each release snapshot lives at `src/aio/agent_commands/{agent}/{version}/`
  (e.g., `claude/v2/INIT_PHASE.md`).
- Prompt changes MUST include a CHANGELOG entry and version bump (v2 → v3).
- The CLI `--agent-version` flag MUST support using prior versions (backward
  compatibility).
- Prompts are vendored in zipapp/PyInstaller distributions; no external
  dependencies.

**Rationale**: Live-fetched prompts break reproducibility and create a dependency
that conflicts with the offline-first guarantee. Users must be able to trust that
a given AIO version produces the same output six months later.

---

### XII. Four Distribution Modes (Ubiquity Law)

AIO MUST work identically in all four distribution modes. None is "limited" or
"beta":

1. **Zero-Install** — copy `src/aio/` to any directory, run `python -m aio --help`
2. **Zipapp** (`.pyz`) — single file, `python aio.pyz --help`
3. **PyInstaller** (`.exe` / `.bin`) — standalone binary, `./aio --help`
4. **Pip** — `pip install aio`, `aio --help`

- All imports MUST be absolute — no relative imports.
- No `sys.path` manipulation anywhere.
- CI/CD MUST test all 4 modes on Windows, macOS, and Linux before any release.
- Automated distribution via GitHub Actions: zipapp + exe + PyPI.

**Rationale**: Requiring Python to use a Python tool is a real barrier for many
users. The binary and zipapp modes eliminate it without compromising the pip
experience.

---

## Technical Constraints

### Logging & Observability

- Stderr: structured logs (level, component, message). No uncontrolled `print()`.
- Stdout: RESERVED for piping (e.g., `aio build | jq`).
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
- Optional log file: `~/.aio/logs/aio.log` (weekly rotation).

### Performance Targets

- Full build for 30 slides MUST complete in < 30 seconds (i5, 8 GB RAM).
- Hot-reload in `serve` mode MUST complete in < 2 seconds.
- Image generation (Pollinations.ai) MUST be async and non-blocking.
- Markdown parsing MUST complete in < 500 ms for 100 slides.

### Security

- YAML frontmatter MUST use `yaml.safe_load()` — no arbitrary code execution.
- SVG output MUST be sanitized — no `<script>` tags allowed in SVG.
- All URLs MUST be validated before HTTP requests.
- HTML output MUST be escaped to prevent XSS from user-supplied content.

---

## Implementation Milestones

| Milestone | Focus | Coverage Target |
|-----------|-------|-----------------|
| **M0** (Weeks 1–2) | Scaffold, CLI skeleton, 3 base themes, Composition Engine skeleton | 20% |
| **M1** (Weeks 3–4) | 8 core layouts, layout inference, Reveal.js 5.x integration, Claude v1 agent | 50% |
| **M2** (Weeks 5–6) | DataViz engine (SVG charts), ~200 Lucide icons, robust extract.py | 65% |
| **M2.5** (Week 7) | SVG Composites, Pollinations.ai `--enrich`, all 8 agent templates | 75% |
| **M3** (Weeks 8–9) | Prompt v2, auto-layout, speaker notes, responsive SVG | 80% |
| **M4** (Weeks 10–12) | 8 additional layouts, animations, 64+ themes, alpha release | 80%+ |

---

## Amendment Process

All structural changes to this constitution MUST follow this procedure:

1. **Proposal** — GitHub issue tagged `[constitution]` arguing why an Article is
   inadequate.
2. **Discussion** — Public comments; 48-hour minimum debate window.
3. **Vote** — Maintainer supermajority (2/3) required to accept.
4. **Merge** — Amendment merged, versioned in CHANGELOG, reflected in next release.
5. **Effective** — New constitution takes effect on the next version tag.

**Immutable Articles** (require hard fork to change):
- Article I (Python 3.12+)
- Article II (Offline HTML)
- Article III (Visual Intelligence as core)
- Article VIII (Reveal.js 5.x)

---

## Governance

- This constitution supersedes all other guidelines and practices in the AIO
  repository. In case of conflict, the constitution wins.
- Every PR MUST be reviewed against the Constitution Check in `plan.md` before
  merge. Violations require explicit justification in the Complexity Tracking
  table.
- `CONSTITUTION_VERSION` follows semantic versioning:
  - **MAJOR**: backward-incompatible principle removals or redefinitions.
  - **MINOR**: new principle or section added / materially expanded.
  - **PATCH**: clarifications, wording, non-semantic refinements.
- Compliance review is expected at each milestone boundary (M0, M1, M2, M2.5, M3, M4).
- Runtime development guidance: see `CLAUDE.md` at repository root.

**Version**: 1.0.0 | **Ratified**: 2026-04-11 | **Last Amended**: 2026-04-11
