"""AIO `theme` command group — list, search, info, use, show, create."""
# NOTE: NO `from __future__ import annotations` in this file.
# Typer relies on runtime type introspection; postponed evaluation breaks it.

import difflib
import json
import os
import re
import shutil
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from aio._log import get_logger
from aio.themes.loader import ThemeRecord, load_registry
from aio.themes.validator import validate_theme

_log = get_logger(__name__)
console = Console(stderr=False)

app = typer.Typer(name="theme", help="Theme management (list, search, info, use, show, create)")

# Minimum fuzzy match score for --search
_SEARCH_THRESHOLD = 0.3


def _fuzzy_score(query: str, record: ThemeRecord) -> float:
    """Compute a [0.0, 1.0] relevance score for a theme record against query."""
    q = query.lower()
    # Direct substring match on id/name → boost
    if q in record.id.lower():
        id_score = 1.0
    else:
        id_score = difflib.SequenceMatcher(None, q, record.id.lower()).ratio() + 0.1
    if q in record.name.lower():
        name_score = 1.0
    else:
        name_score = difflib.SequenceMatcher(None, q, record.name.lower()).ratio()
    # Category match
    cat_score = 1.0 if any(q in c.lower() for c in record.categories) else 0.0
    return min(max(id_score, name_score, cat_score), 1.0)


def _filter_themes(
    registry: list[ThemeRecord],
    filter_tags: str | None,
    search: str | None,
    limit: int,
) -> list[ThemeRecord]:
    """Apply tag filter → fuzzy search → limit."""
    results = list(registry)

    if filter_tags:
        tags = {t.strip().lower() for t in filter_tags.split(",") if t.strip()}
        results = [r for r in results if tags & {c.lower() for c in r.categories}]

    if search:
        scored = [(r, _fuzzy_score(search, r)) for r in results]
        scored = [(r, s) for r, s in scored if s >= _SEARCH_THRESHOLD]
        scored.sort(key=lambda x: x[1], reverse=True)
        results = [r for r, _ in scored]

    return results[:limit]


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


@app.command("list")
def list_themes(
    limit: int = typer.Option(20, "--limit", help="Maximum number of themes to show"),
    filter_tags: str | None = typer.Option(None, "--filter", help="Comma-separated tag filter"),
    search: str | None = typer.Option(None, "--search", help="Fuzzy name/id search"),
    output_json: bool = typer.Option(False, "--json", is_flag=True, help="Output JSON"),
) -> None:
    """List available themes with optional filtering."""
    registry = load_registry()
    results = _filter_themes(registry, filter_tags, search, limit)

    if output_json:
        data = [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "categories": r.categories,
                "author": r.author,
                "source_url": r.source_url,
                "colors": r.colors,
                "typography": r.typography,
            }
            for r in results
        ]
        typer.echo(json.dumps(data, indent=2))
        return

    table = Table(title=f"Available Themes ({len(results)} of {len(registry)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Categories")
    table.add_column("Source")
    table.add_column("Description")
    for r in results:
        table.add_row(
            r.id,
            r.name,
            ", ".join(r.categories),
            "builtin" if r.is_builtin else (r.source_url or ""),
            r.description[:60],
        )
    console.print(table)
    _log.info("Command complete")


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


@app.command("search")
def search_themes(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", help="Maximum results"),
    output_json: bool = typer.Option(False, "--json", is_flag=True, help="Output JSON"),
) -> None:
    """Search themes by name, ID, or category."""
    registry = load_registry()
    scored = [(r, _fuzzy_score(query, r)) for r in registry]
    scored = [(r, s) for r, s in scored if s >= _SEARCH_THRESHOLD]
    scored.sort(key=lambda x: x[1], reverse=True)
    results = scored[:limit]

    if output_json:
        data = [
            {
                "id": r.id,
                "name": r.name,
                "categories": r.categories,
                "score": round(s, 2),
            }
            for r, s in results
        ]
        typer.echo(json.dumps(data, indent=2))
        return

    table = Table(title=f"Search results for '{query}'")
    table.add_column("Score", justify="right")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Categories")
    for r, s in results:
        table.add_row(f"{s:.2f}", r.id, r.name, ", ".join(r.categories))
    console.print(table)
    _log.info("Command complete")


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------


@app.command("info")
def info(
    theme_id: str = typer.Argument(..., help="Theme ID"),
    output_json: bool = typer.Option(False, "--json", is_flag=True, help="Output JSON"),
) -> None:
    """Show detailed theme information."""
    registry = load_registry()
    record = next((r for r in registry if r.id == theme_id), None)
    if record is None:
        _log.error("Theme '%s' not found.", theme_id)
        raise typer.Exit(code=2)

    if output_json:
        data = {
            "id": record.id,
            "name": record.name,
            "description": record.description,
            "version": record.version,
            "author": record.author,
            "source_url": record.source_url,
            "categories": record.categories,
            "colors": record.colors,
            "typography": record.typography,
            "is_builtin": record.is_builtin,
        }
        typer.echo(json.dumps(data, indent=2))
        return

    # Read agent prompt snippet from section 11 (if DESIGN.md present)
    agent_snippet = ""
    if record.design_md_path and record.design_md_path.exists():
        from aio.themes.parser import parse_design_md

        try:
            sections = parse_design_md(record.design_md_path.read_text(encoding="utf-8"))
            agent_snippet = sections[10].raw_content[:300]
        except Exception:
            pass

    colors_str = "\n".join(f"  {k}: {v}" for k, v in record.colors.items())
    typo_str = "\n".join(f"  {k}: {v}" for k, v in record.typography.items())
    body = (
        f"[bold]ID:[/bold]          {record.id}\n"
        f"[bold]Name:[/bold]        {record.name}\n"
        f"[bold]Author:[/bold]      {record.author}\n"
        f"[bold]Categories:[/bold]  {', '.join(record.categories)}\n"
        f"[bold]Source:[/bold]      {record.source_url or 'builtin'}\n\n"
        f"[bold]Colors:[/bold]\n{colors_str}\n\n"
        f"[bold]Typography:[/bold]\n{typo_str}"
    )
    if agent_snippet:
        body += f"\n\n[bold]Agent Prompt:[/bold]\n{agent_snippet}"

    console.print(Panel(body, title=f"Theme: {record.name}"))
    _log.info("Command complete")


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


@app.command("show")
def show(
    theme_id: str = typer.Argument(..., help="Theme ID"),
    section: int | None = typer.Option(None, "--section", help="Section number (1–12)"),
    raw: bool = typer.Option(False, "--raw", is_flag=True, help="Print raw Markdown"),
) -> None:
    """Display a theme's DESIGN.md (or a specific section)."""
    registry = load_registry()
    record = next((r for r in registry if r.id == theme_id), None)
    if record is None:
        _log.error("Theme '%s' not found.", theme_id)
        raise typer.Exit(code=2)

    if record.design_md_path is None or not record.design_md_path.exists():
        _log.error("Theme '%s' has no DESIGN.md.", theme_id)
        raise typer.Exit(code=4)

    text = record.design_md_path.read_text(encoding="utf-8")

    if section is not None:
        if not (1 <= section <= 12):
            _log.error("Section %d out of range (1–12).", section)
            raise typer.Exit(code=3)
        from aio.themes.parser import parse_design_md

        try:
            sections = parse_design_md(text)
        except Exception as exc:
            _log.error("Failed to parse DESIGN.md: %s", exc)
            raise typer.Exit(code=4) from exc
        matching = [s for s in sections if s.section_number == section]
        if not matching:
            raise typer.Exit(code=3)
        text = f"## {section}. {matching[0].heading}\n\n{matching[0].raw_content}"

    if raw:
        typer.echo(text)
    else:
        console.print(Markdown(text))
    _log.info("Command complete")


# ---------------------------------------------------------------------------
# use
# ---------------------------------------------------------------------------


@app.command("use")
def use(
    theme_id: str = typer.Argument(..., help="Theme ID to activate"),
    project_dir: str = typer.Option(".", "--project-dir", help="Project root directory"),
) -> None:
    """Set the active theme for the current project."""
    registry = load_registry()
    record = next((r for r in registry if r.id == theme_id), None)
    if record is None:
        _log.error("Theme '%s' not found in global registry.", theme_id)
        raise typer.Exit(code=2)

    aio_dir = Path(project_dir) / ".aio"
    if not aio_dir.exists():
        _log.error("No .aio/ directory found in '%s'. Run aio init first.", project_dir)
        raise typer.Exit(code=3)

    config_path = aio_dir / "config.yaml"
    if config_path.exists():
        config_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    else:
        config_data = {}

    config_data["theme"] = theme_id
    config_path.write_text(yaml.dump(config_data, default_flow_style=False), encoding="utf-8")

    # Copy theme metadata to per-project registry
    themes_dir = aio_dir / "themes"
    themes_dir.mkdir(exist_ok=True)
    project_registry_path = themes_dir / "registry.json"
    entry = {
        "id": record.id,
        "name": record.name,
        "description": record.description,
        "colors": record.colors,
        "typography": record.typography,
        "categories": record.categories,
    }
    project_registry_path.write_text(json.dumps([entry], indent=2), encoding="utf-8")

    typer.echo(f"Theme '{theme_id}' activated. Rebuild with: aio build slides.md")
    _log.info("Command complete")


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

_BLANK_DESIGN_MD = """\
# {name} — DESIGN.md

## 1. Visual Theme

Describe the overall aesthetic and visual identity of this theme.

## 2. Color Palette

```yaml
primary: "#1a1a1a"
accent: "#0066cc"
background: "#ffffff"
text: "#1a1a1a"
```

- Primary: #1a1a1a
- Accent: #0066cc

## 3. Typography

```yaml
heading_font: "sans-serif"
body_font: "sans-serif"
```

## 4. Components

Describe buttons, cards, badges, and other UI components.

## 5. Layout System

Grid, spacing, and max-width guidelines.

## 6. Depth & Shadows

Shadow definitions and usage guidelines.

## 7. Do's & Don'ts

List dos and don'ts for this design system.

## 8. Responsive Behavior

Breakpoints and responsive layout rules.

## 9. Animation & Transitions

Default transitions and motion guidelines.

## 10. Accessibility

WCAG compliance targets and focus indicator styles.

## 11. Agent Prompt Snippet

Provide a 200-word description for AI agents generating content in this theme.
Describe the visual character, color usage, typography rules, and layout preferences.
Include guidance on which layouts work best and what content tone fits the design.
"""

_BLANK_THEME_CSS = """\
:root {
  --color-primary: #1a1a1a;
  --color-accent: #0066cc;
  --color-background: #ffffff;
  --color-text: #1a1a1a;
  --font-display: sans-serif;
  --font-body: sans-serif;
}
"""

_BLANK_LAYOUT_CSS = """\
.layout-hero-title h1.hero-title {
  color: var(--color-primary);
  font-family: var(--font-display);
}

.layout-stat-highlight .stat {
  color: var(--color-accent);
  font-family: var(--font-display);
  font-size: 5rem;
}

.layout-content {
  font-family: var(--font-body);
}
"""


@app.command("create")
def create(
    name: str = typer.Argument(..., help="New theme name (lowercase letters, digits, hyphens)"),
    from_theme: str | None = typer.Option(None, "--from", help="Source theme ID to copy from"),
    project_dir: str = typer.Option(".", "--project-dir", help="Project root directory"),
    edit: bool = typer.Option(False, "--edit", is_flag=True, help="Open DESIGN.md in $EDITOR after creation"),
) -> None:
    """Create a new theme scaffold in the current project."""
    if not _NAME_RE.match(name):
        _log.error("Invalid theme name '%s'. Use lowercase letters, digits, and hyphens only.", name)
        raise typer.Exit(code=4)

    aio_dir = Path(project_dir) / ".aio"
    themes_dir = aio_dir / "themes"

    dest = themes_dir / name
    if dest.exists():
        _log.error("Theme '%s' already exists at %s.", name, dest)
        raise typer.Exit(code=3)

    dest.mkdir(parents=True)

    if from_theme:
        registry = load_registry()
        source = next((r for r in registry if r.id == from_theme), None)
        if source is None:
            _log.error("Source theme '%s' not found.", from_theme)
            dest.rmdir()
            raise typer.Exit(code=2)
        # Copy theme files
        for filename in ("DESIGN.md", "theme.css", "layout.css", "meta.json"):
            src_file = source.base_dir / filename
            if src_file.exists():
                shutil.copy2(src_file, dest / filename)
        typer.echo(f"Theme '{name}' created based on '{from_theme}' at {dest}")
    else:
        # Scaffold from blank template
        (dest / "DESIGN.md").write_text(_BLANK_DESIGN_MD.format(name=name), encoding="utf-8")
        (dest / "theme.css").write_text(_BLANK_THEME_CSS, encoding="utf-8")
        (dest / "layout.css").write_text(_BLANK_LAYOUT_CSS, encoding="utf-8")
        meta: dict[str, object] = {
            "id": name,
            "name": name.replace("-", " ").title(),
            "description": "",
            "version": "1.0.0",
            "author": "",
            "source_url": None,
            "categories": [],
            "colors": {"primary": "#1a1a1a", "accent": "#0066cc", "background": "#ffffff", "text": "#1a1a1a"},
            "typography": {"heading_font": "sans-serif", "body_font": "sans-serif"},
            "is_builtin": False,
        }
        (dest / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        typer.echo(f"Theme '{name}' created at {dest}")

    # List created files
    for f in sorted(dest.iterdir()):
        typer.echo(f"  {f.name}")

    if edit:
        editor = os.environ.get("EDITOR", "")
        if editor:
            os.system(f'{editor} "{dest / "DESIGN.md"}"')
        else:
            _log.warning("$EDITOR not set — skipping auto-open.")

    _log.info("Command complete")


# ---------------------------------------------------------------------------
# validate (keep existing)
# ---------------------------------------------------------------------------


@app.command("validate")
def validate(
    theme_id: str = typer.Argument(..., help="Theme ID to validate"),
    check_css: bool = typer.Option(False, "--css", help="Also validate theme.css with cssutils and WCAG contrast"),
) -> None:
    """Validate a theme's DESIGN.md against the 11-section schema."""
    errors = validate_theme(theme_id, check_css=check_css)
    if errors:
        for err in errors:
            _log.error("%s", err)
        typer.echo(f"✗ Theme '{theme_id}' has {len(errors)} validation error(s).", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"✓ Theme '{theme_id}' is valid.")
    _log.info("Command complete")
