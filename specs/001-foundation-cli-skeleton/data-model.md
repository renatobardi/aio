# Data Model: AIO Foundation & CLI Skeleton (M0)

**Phase 1 Output** | **Date**: 2026-04-11 | **Plan**: `specs/001-foundation-cli-skeleton/plan.md`

---

## Core Entities

### ProjectConfig

Immutable, validated config loaded from `.aio/config.yaml`.
Produced by `ProjectConfig.load(dir_path)` in `src/aio/commands/init.py`.

```python
@dataclass(frozen=True)
class ProjectConfig:
    agent: str                  # One of SUPPORTED_AGENTS
    theme: str = "default"      # Theme ID from registry
    enrich: bool = False        # Image generation enabled
    serve_port: int = 8000      # HTTP port for aio serve
    output_dir: str = "build"   # Output directory (relative to project root)
```

| Field | Type | Default | Validation |
|-------|------|---------|-----------|
| `agent` | `str` | (required) | Must be in `SUPPORTED_AGENTS` set |
| `theme` | `str` | `"default"` | Must exist in `.aio/themes/registry.json` |
| `enrich` | `bool` | `False` | YAML bool coercion applied |
| `serve_port` | `int` | `8000` | Must be 1–65535 |
| `output_dir` | `str` | `"build"` | Normalized to relative path |

**Validation rules:**
- `agent` validated against `SUPPORTED_AGENTS = frozenset({"claude", "gemini", "copilot", "windsurf", "devin", "chatgpt", "cursor", "generic"})`
- Invalid agent → `ValueError("agent must be one of [...]. Got '{value}'")`
- Absolute `output_dir` → normalized to relative to `.aio/` parent directory
- YAML parsed with `yaml.safe_load()` exclusively

---

### SlideAST

Internal representation of one parsed slide. Produced by the parser for each `---`-delimited section.

| Field | Type | Description |
|-------|------|-------------|
| `index` | `int` | Zero-based slide position in the deck |
| `frontmatter` | `dict[str, Any]` | Deck-level YAML (from first slide only; `{}` for others) |
| `title` | `str \| None` | First `# Heading` extracted from body |
| `body_tokens` | `list[Token]` | mistune 3.x AST tokens for the slide body |
| `metadata` | `dict[str, str]` | Per-slide `<!-- @key: value -->` tags |
| `raw_markdown` | `str` | Original markdown source before parsing (for debugging) |

**Validation rules:**
- `frontmatter` parsed with `yaml.safe_load()` from the first `---` block only
- `body_tokens` is never `None`; empty list for title-only slides
- `metadata` keys are lowercased; values are stripped strings
- `<!-- @: invalid -->` (empty key) → silently ignored; WARNING logged

---

### LayoutRecord

One entry in the auto-discovered layout registry. Populated at module import from `src/aio/layouts/`.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Layout identifier (e.g., `"hero-title"`) — derived from filename stem |
| `path` | `str` | Resource path usable with `importlib.resources.files()` |
| `blocks` | `list[str]` | Named blocks found via `{% block name %}` regex scan |

**Validation rules:**
- `name` is the `.j2` filename stem (e.g., `hero-title.j2` → `"hero-title"`)
- `blocks` extracted via `re.findall(r'\{%-?\s*block\s+(\w+)\s*-?%\}', content)`
- Duplicate block names in one template → WARNING logged; last definition wins
- Empty `blocks` list is valid (zero-block templates allowed)

---

### AgentCommandTemplate

In-memory representation of a loaded agent prompt template for one command+agent pair.

| Field | Type | Description |
|-------|------|-------------|
| `command` | `str` | One of: `outline`, `generate`, `refine`, `visual`, `theme`, `extract`, `build` |
| `agent` | `str` | One of the 8 supported agents |
| `content` | `str` | Formatted prompt text after agent-specific conversion |
| `has_system_prompt` | `bool` | Whether the content includes a distinct system section |

**Validation rules:**
- `command` must be in `SUPPORTED_COMMANDS` registry
- `content` is never empty; if template file is missing, `FileNotFoundError` is raised at load time
- Format conversion is stateless: same inputs → same output (deterministic)

---

### ThemeRegistryEntry

One entry in `src/aio/themes/registry.json` (global) or `.aio/themes/registry.json` (per-project).

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Slug (e.g., `"minimal"`) — unique |
| `name` | `str` | Human display name |
| `description` | `str` | One-line summary |
| `tags` | `list[str]` | e.g., `["minimal", "corporate"]` |
| `author` | `str` | Theme author |
| `source` | `str` | `"builtin"` or `"awesome-design-md"` |
| `path` | `str` | Relative path to theme directory |
| `created_at` | `str` | ISO 8601 |
| `updated_at` | `str` | ISO 8601 |

---

### DeckFrontmatter

Parsed representation of the deck-level YAML block at the top of `slides.md`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `title` | `str` | `"Untitled"` | Presentation title |
| `author` | `str \| None` | `None` | Author name |
| `theme` | `str` | From `ProjectConfig` | Theme ID override |
| `agent` | `str` | From `ProjectConfig` | Agent override |

---

## State Transitions

### `aio init` States

```
USER INVOKES aio init [name]
    │
    ▼ validate args (agent, theme)
VALIDATED
    │  ← exits with code 1 if agent/theme invalid
    ▼ check .aio/ exists
NOT_EXISTS
    │  ← exits with error if exists and no --force
    ▼ create directory structure
FILES_CREATED
    │
    ▼ write config.yaml, meta.json, slides.md, themes/registry.json
WRITTEN
    │
    ▼ stdout: project path
DONE (exit 0)
```

### `ProjectConfig.load()` States

```
YAML FILE
    │
    ▼ yaml.safe_load()
DICT
    │
    ▼ apply defaults (theme, enrich, serve_port, output_dir)
DICT_WITH_DEFAULTS
    │
    ▼ validate agent membership
VALIDATED
    │  ← raises ValueError if invalid
    ▼ construct @dataclass(frozen=True)
ProjectConfig INSTANCE (immutable)
```

### Slide Parser States

```
RAW slides.md
    │
    ▼ split on "\n---\n"
BLOCKS list
    │
    ▼ block[0]: extract YAML frontmatter via yaml.safe_load()
FRONTMATTER dict
    │
    ▼ for each block: extract <!-- @key: value --> tags
METADATA dict per slide
    │
    ▼ for each block: strip @tags, pass remainder to mistune
BODY_TOKENS list per slide
    │
    ▼ construct SlideAST for each slide
SlideAST list
```

---

## File System Artifacts (M0)

```
.aio/
├── config.yaml            # ProjectConfig fields in YAML
├── meta.json              # { project_name, created_at, version, author? }
└── themes/
    └── registry.json      # Single-theme subset of global registry

~/.aio/
└── logs/
    └── aio.log            # Rotating weekly log (stderr structured text)
```

**`config.yaml` schema:**
```yaml
agent: claude          # required
theme: minimal         # optional, default: "default"
enrich: false          # optional, default: false
serve_port: 8000       # optional, default: 8000
output_dir: build      # optional, default: "build"
```

**`meta.json` schema:**
```json
{
  "project_name": "my-deck",
  "created_at": "2026-04-11T10:00:00Z",
  "version": "0.1.0",
  "author": null
}
```
