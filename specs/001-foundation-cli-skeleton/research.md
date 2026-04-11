# Research: AIO Foundation & CLI Skeleton (M0)

**Phase 0 Output** | **Date**: 2026-04-11 | **Plan**: `specs/001-foundation-cli-skeleton/plan.md`

All technology decisions for this feature are inherited from the project-level research at
`specs/main/research.md`. No NEEDS CLARIFICATION items were open at spec inception.

This document captures the M0-specific decisions and implementation choices not covered
by the project-level research.

---

## Decision Log

### Layout Auto-Discovery Mechanism

**Decision:** `importlib.resources.files()` + `re.finditer()` at module import time
**Rationale:** `importlib.resources` is the only mechanism that works correctly across
all 4 distribution modes (zero-install, zipapp, PyInstaller, pip). `os.scandir()` and
`__file__`-relative paths fail inside zipapp and PyInstaller bundles.
**Alternatives considered:**
- `os.scandir(Path(__file__).parent / "layouts")` — fails in zipapp/PyInstaller
- `pkgutil.iter_modules()` — enumerates Python packages, not `.j2` files
- Explicit registry dict (manual) — rejected; defeats auto-discovery requirement in FR-116

---

### Fuzzy Layout Suggestion

**Decision:** `difflib.get_close_matches(name, registry, n=1, cutoff=0.6)`
**Rationale:** stdlib module, no extra dependency. Sufficient for short layout names
(< 30 chars). `cutoff=0.6` gives useful suggestions without false positives.
**Alternatives considered:**
- `fuzzywuzzy` / `rapidfuzz` — external dep; overkill for 16 short names
- Edit distance (Levenshtein) — can implement manually, but difflib is equivalent
  and already imported

---

### Slide Splitting Strategy

**Decision:** `content.split("\n---\n")` (string split, not regex)
**Rationale:** Simple, O(n), no catastrophic backtracking risk (FR-126). Handles the
Reveal.js separator convention directly. The `---` inside code fences is handled by
stripping frontmatter before splitting — frontmatter occupies the first block and
contains no body `---` separator.
**Edge case:** `---` inside a Markdown code block (` ``` `) is treated as content
because it appears AFTER the first `---\n` split only if in positions > 0. Mitigation:
document that `---` slide separators must be at column 0 on an otherwise-blank line.
**Alternatives considered:**
- regex split — unnecessary complexity; catastrophic backtracking risk on large files
- mistune's built-in splitting — mistune 3.0 does not natively split slides

---

### Agent Template Access at Runtime

**Decision:** `importlib.resources.files("aio.agent_commands")`
**Rationale:** Works in all 4 distribution modes. Files are declared in `pyproject.toml`
under `[tool.setuptools.package-data]`. Accessing files via the importlib API avoids
`__file__`-relative path hacking that fails in frozen executables.
**Alternatives considered:**
- `Path(__file__).parent / "agent_commands"` — fails in PyInstaller one-file mode
- `pkg_resources.resource_string()` — deprecated; prefer importlib.resources

---

### ProjectConfig Immutability

**Decision:** `@dataclass(frozen=True)` with manual `__post_init__` validation
**Rationale:** `frozen=True` makes instances hashable and prevents accidental mutation
without requiring a separate `@property`-based API. `__post_init__` validates agent
membership before the object is fully constructed, so invalid configs can never exist.
**Alternatives considered:**
- `NamedTuple` — no default values, no `__post_init__`; requires more boilerplate
- `pydantic.BaseModel` — adds a heavy dependency (> 5 MB); not in core dep list

---

### Log Format

**Decision:** `"%(levelname)s [%(name)s] %(message)s"` to stderr via `logging.StreamHandler`
**Rationale:** Simple, structured, grep-friendly. The `%(name)s` field (module logger name)
identifies which component emitted the message. No JSON format required for M0; structured
JSON logging deferred to post-M4 if observability tools need it.
**Alternatives considered:**
- `structlog` — excellent structured logging, but adds a dependency not in the core list
- JSON format — harder to read in terminal; no tooling requirement at M0

---

### Clipboard Support for `--copy` Flag

**Decision:** `pyperclip` with graceful fallback to stdout; `pyperclip` added as an
optional dep under `[commands]` extra
**Rationale:** `pyperclip` is the de facto cross-platform clipboard library for Python.
It is tiny (< 20 KB) and covers macOS/Linux/Windows. Falling back to stdout when
`pyperclip.PyperclipException` is raised satisfies the US7 acceptance scenario without
crashing.
**Alternatives considered:**
- `subprocess` + `pbcopy`/`xclip` — platform-specific; fragile on CI
- Omit `--copy` entirely — violates FR-137

---

## All Clarifications Resolved

| Item | Status |
|------|--------|
| Layout discovery mechanism | ✅ `importlib.resources.files()` |
| Fuzzy match algorithm | ✅ `difflib.get_close_matches()` |
| Slide splitting | ✅ `str.split("\n---\n")` |
| Template access at runtime | ✅ `importlib.resources.files()` |
| Config immutability approach | ✅ `@dataclass(frozen=True)` + `__post_init__` |
| Log format | ✅ `levelname [name] message` to stderr |
| Clipboard for `--copy` | ✅ `pyperclip` + stdout fallback |
