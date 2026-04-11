# CLI Contract: AIO

**Phase 1 Output** | **Date**: 2026-04-11 | **Plan**: `specs/main/plan.md`

This document defines the public CLI interface for `aio`. It is the contract between the
command implementation and any user, script, CI pipeline, or agent that invokes `aio`.

---

## Global Flags

```
aio [--agent AGENT] [--agent-version VERSION] [--verbose] [--quiet] COMMAND [args...]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--agent` | str | `"claude"` | AI agent to use for prompt templates |
| `--agent-version` | str | `"v1"` | Agent prompt version |
| `--verbose` | flag | off | Set log level to DEBUG |
| `--quiet` | flag | off | Set log level to ERROR (suppress INFO) |

---

## Commands

### `aio init [NAME] [--theme THEME_ID]`

Scaffold a new AIO presentation project.

**Arguments:**
- `NAME` (optional) — project name; defaults to current directory name

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--theme` | str | `"minimal"` | Theme ID to use |

**Exit codes:**
- `0` — Success; `.aio/` created
- `1` — Theme ID not found in registry

**Stdout:** Path to created `.aio/` directory (pipeable)
**Stderr:** Progress logs (INFO level)

---

### `aio build INPUT [--output OUTPUT] [--theme THEME_ID] [--enrich] [--provider PROVIDER]`

Build a standalone HTML presentation from a Markdown file.

**Arguments:**
- `INPUT` — path to input `.md` file (required)

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output`, `-o` | path | `INPUT_stem.html` | Output HTML file path |
| `--theme` | str | From `.aio/config.yaml` | Override theme |
| `--enrich` | flag | off | Generate and embed images via enrichment API |
| `--provider` | str | `"pollinations"` | Image provider when `--enrich` active |
| `--skip-existing` | flag | off | Skip image generation if already present |

**Exit codes:**
- `0` — Success; HTML file written
- `1` — Parse error (invalid frontmatter, missing required field)
- `2` — Theme not found
- `3` — External URL detected in output (Art. II violation)
- `4` — Enrichment provider unreachable (non-fatal when SVG fallback active — returns 0)

**Stdout:** Path to generated HTML file (pipeable: `aio build slides.md | xargs open`)
**Stderr:** Build progress, timing, warnings

---

### `aio serve INPUT [--port PORT] [--host HOST] [--no-reload]`

Serve a presentation with hot reload.

**Arguments:**
- `INPUT` — path to input `.md` file

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--port` | int | `3000` | HTTP port |
| `--host` | str | `"127.0.0.1"` | Bind address |
| `--no-reload` | flag | off | Disable file watching |

**Behavior:**
- Watches `INPUT` and the `.aio/` directory for changes
- Hot reload MUST complete in < 2 seconds (per constitution Art. III performance requirement)
- Prints URL to stderr on startup: `Serving at http://127.0.0.1:3000`

**Exit codes:**
- `0` — Server stopped by user (Ctrl+C)
- `1` — Port already in use

---

### `aio theme SUBCOMMAND`

Manage themes.

#### `aio theme list [--tags TAG,...] [--source SOURCE]`

List available themes.

| Option | Type | Description |
|--------|------|-------------|
| `--tags` | str | Filter by tag(s), comma-separated |
| `--source` | str | `"builtin"` or `"awesome-design-md"` |

**Stdout:** Table of `ID | Name | Tags | Source` (Rich table)

#### `aio theme info THEME_ID`

Show DESIGN.md snippet and metadata for a theme.

**Exit codes:** `0` OK, `1` not found.

#### `aio theme validate THEME_ID`

Validate a theme's `DESIGN.md` against JSON schema (all 11 sections present and well-formed).

**Exit codes:** `0` valid, `1` invalid (errors printed to stderr).

---

### `aio extract URL [--output OUTPUT] [--timeout SECONDS]`

Scrape a design website and generate a `DESIGN.md` file.

**Arguments:**
- `URL` — Target URL (validated before HTTP request)

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output`, `-o` | path | `./DESIGN.md` | Output file |
| `--timeout` | int | `30` | HTTP request timeout in seconds |

**Exit codes:**
- `0` — DESIGN.md written
- `1` — Network error
- `2` — Parsing failed (could not extract enough sections)

---

### `aio enrich INPUT [--output OUTPUT] [--provider PROVIDER] [--skip-existing]`

Generate images for slides and embed them in the Markdown source.

**Arguments:**
- `INPUT` — path to input `.md` file

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output`, `-o` | path | `INPUT_stem-enriched.md` | Output Markdown path |
| `--provider` | str | `"pollinations"` | Image provider |
| `--skip-existing` | flag | off | Skip if slide already has an image |

**Exit codes:** `0` success, `1` all providers unreachable (fallback SVG written).

---

## Stdout/Stderr Contract

| Stream | Content | Notes |
|--------|---------|-------|
| **stdout** | Machine-readable output only | File paths, JSON (`--json` flag where applicable) |
| **stderr** | Structured log lines | Format: `LEVEL [component] message` |

This separation allows: `aio build slides.md | xargs open` and `aio build slides.md 2>/dev/null`.
No `print()` calls are permitted in production code — use `_log.py` exclusively.
