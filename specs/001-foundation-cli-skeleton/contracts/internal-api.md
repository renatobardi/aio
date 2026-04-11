# Internal API Contracts: AIO Foundation & CLI Skeleton (M0)

**Phase 1 Output** | **Date**: 2026-04-11 | **Plan**: `specs/001-foundation-cli-skeleton/plan.md`

This document defines the public Python API contracts for M0 modules. These are the interfaces
between modules — not the CLI interface (covered in `specs/main/contracts/cli-contract.md`).

---

## `src/aio/commands/init.py`

### `ProjectConfig`

```python
@dataclass(frozen=True)
class ProjectConfig:
    agent: str
    theme: str = "default"
    enrich: bool = False
    serve_port: int = 8000
    output_dir: str = "build"

    def __post_init__(self) -> None:
        """Validate agent membership. Raises ValueError on invalid agent."""

    @classmethod
    def load(cls, dir_path: str | Path) -> "ProjectConfig":
        """
        Load and validate config from {dir_path}/config.yaml.

        Raises:
            FileNotFoundError: if config.yaml does not exist
            ValueError: if agent is not in SUPPORTED_AGENTS
            yaml.YAMLError: if YAML is malformed
        """

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict representation (for serialization)."""
```

**Contract:**
- `load()` MUST use `yaml.safe_load()` — never `yaml.load()`
- `load()` applies defaults before validation
- The returned instance is immutable — any mutation raises `FrozenInstanceError`
- `load()` completes in < 10ms (SC-106)

---

## `src/aio/composition/engine.py`

### `CompositionEngine`

```python
class CompositionEngine:
    layout_registry: dict[str, LayoutRecord]

    def __init__(self) -> None:
        """Auto-discover all .j2 files in src/aio/layouts/ at construction time."""

    def infer_layout(self, slide: SlideAST) -> str:
        """
        Return the layout name for the given slide.

        Priority:
          1. slide.metadata.get("layout") — explicit override
          2. Heuristic inference from body_tokens (stub in M0: returns "content")

        Raises:
            LayoutNotFoundError: if layout name is not in registry
        """

    def render(self, slide: SlideAST, layout_name: str, context: dict[str, Any]) -> str:
        """
        Render a slide using the named layout template with given context.

        Returns: HTML string
        Raises:
            LayoutNotFoundError: if layout_name not in registry
            jinja2.TemplateError: on render failure
        """
```

**Contract:**
- `CompositionEngine` is stateless after construction — thread-safe for concurrent renders
- `infer_layout()` never mutates `slide`
- `render()` is deterministic: same inputs → same output
- `render()` completes in < 1ms per slide (SC-110)

### `LayoutRecord`

```python
@dataclass(frozen=True)
class LayoutRecord:
    name: str       # e.g., "hero-title"
    path: str       # importlib.resources path
    blocks: list[str]  # e.g., ["title", "subtitle"]
```

### `LayoutNotFoundError`

```python
class LayoutNotFoundError(ValueError):
    """
    Raised when a layout name is not in the registry.
    Includes fuzzy suggestion when available.

    Attributes:
        name: str        — the unknown layout name
        suggestion: str | None — closest match from difflib
    """
```

---

## `src/aio/commands/build.py` (parser portion)

### `parse_slides()`

```python
def parse_slides(path: str | Path) -> list[SlideAST]:
    """
    Parse a slides.md file into a list of SlideAST objects.

    - Splits on "\\n---\\n" separators
    - Extracts YAML frontmatter from the first block only
    - Extracts <!-- @key: value --> metadata from each block
    - Strips metadata tags from body content before mistune parsing

    Raises:
        FileNotFoundError: if path does not exist
        yaml.YAMLError: if frontmatter YAML is invalid (with line reference)

    Performance: O(n) where n = file size; 100 slides < 50ms (SC-104)
    """
```

---

## `src/aio/agents/prompts.py`

### `load_agent_template()`

```python
def load_agent_template(
    agent: str,
    command: str,
    version: str = "v1",
) -> AgentCommandTemplate:
    """
    Load and format the prompt template for the given agent + command.

    Raises:
        ValueError: if agent or command not in supported sets
        FileNotFoundError: if template files are missing from package
    """

def list_agents() -> list[str]:
    """Return the list of supported agent names in alphabetical order."""

def list_commands() -> list[tuple[str, str]]:
    """Return list of (command_name, description) tuples for all 7 commands."""
```

**Contract:**
- `load_agent_template()` MUST NOT make network calls
- Template files are accessed via `importlib.resources.files()` only
- Output is deterministic for the same inputs

---

## `src/aio/_log.py`

### `setup_logging()`

```python
def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root "aio" logger to write structured messages to stderr.

    Format: "%(levelname)s [%(name)s] %(message)s"
    Handler: logging.StreamHandler(sys.stderr)

    Call once at CLI entry point. Idempotent (calling twice does not duplicate handlers).
    """

def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger of the "aio" root logger.

    Usage: _log = get_logger(__name__)
    """
```

**Contract:**
- All aio loggers are children of `"aio"` — filtering at root propagates correctly
- NEVER write to stdout — stderr only
- `setup_logging()` MUST be called before any `get_logger()` call produces visible output

---

## `src/aio/themes/validator.py`

### `validate_theme()`

```python
def validate_theme(theme_id: str) -> list[str]:
    """
    Validate a theme's DESIGN.md for schema compliance.

    Returns: list of error strings (empty if valid)
    Raises:
        ThemeNotFoundError: if theme_id is not in global registry
    """
```

---

## Error Hierarchy

```
AIOError(Exception)
├── ConfigError(AIOError)           — ProjectConfig load/validation failures
├── LayoutNotFoundError(AIOError)   — unknown layout name
├── ThemeNotFoundError(AIOError)    — unknown theme ID
├── ParseError(AIOError)            — slides.md parsing failure
└── AgentError(AIOError)            — agent template loading failure
```

All errors include a human-readable `message` attribute and an optional
`suggestion` attribute for fuzzy-match hints.

---

## Stdout/Stderr Contract (M0 commands)

| Command | Stdout | Stderr |
|---------|--------|--------|
| `aio init` | Absolute path of created directory | Progress INFO logs |
| `aio theme list` | Rich table (theme IDs, names, tags) | INFO logs |
| `aio theme validate` | Nothing | Pass/fail messages |
| `aio commands list` | Plain text list of commands | INFO logs |
| `aio commands [cmd]` | Formatted prompt text | INFO/DEBUG logs |
| `aio --version` | `aio 0.1.0` | Nothing |
| `aio --help` | Help text | Nothing |
