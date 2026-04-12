#!/usr/bin/env python3
"""
Import themes from awesome-design-md into src/aio/themes/.

Usage:
  python scripts/import-awesome-designs.py [--dry-run] [--limit N] [--output DIR]

Options:
  --dry-run         Discover and validate without writing any files
  --limit N         Import at most N themes (default: unlimited)
  --output DIR      Theme output directory (default: src/aio/themes/)
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aio.exceptions import DesignSectionParseError, DesignSectionValidationError
from aio.themes.parser import (
    extract_css_vars,
    extract_layout_css,
    parse_design_md,
)

AWESOME_REPO = "https://github.com/nicholasgasior/awesome-design-md"
REGISTRY_FILENAME = "registry.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
    stream=sys.stderr,
)
_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

def _slugify(name: str) -> str:
    """Convert a theme name to a filesystem-safe slug, e.g. 'Stripe Design' → 'stripe-design'."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug or "unknown"


# ---------------------------------------------------------------------------
# Clone / sync
# ---------------------------------------------------------------------------

def _clone_or_pull(repo_url: str, clone_dir: Path) -> None:
    if (clone_dir / ".git").exists():
        _log.info("Pulling updates in %s", clone_dir)
        subprocess.check_call(
            ["git", "pull", "--ff-only"],
            cwd=clone_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        _log.info("Cloning %s → %s", repo_url, clone_dir)
        subprocess.check_call(
            ["git", "clone", "--depth", "1", repo_url, str(clone_dir)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def _discover_themes(repo_root: Path) -> list[Path]:
    """Return all DESIGN.md paths found under repo_root."""
    return sorted(repo_root.rglob("DESIGN.md"))


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def _extract_meta(design_path: Path, sections: list) -> dict:
    """Build a meta.json dict from parsed DesignSection list and file location."""
    # Derive a human name and slug from the parent directory or section 1 heading
    parent_name = design_path.parent.name
    name = parent_name.replace("-", " ").replace("_", " ").title()
    theme_id = _slugify(parent_name) or "theme"

    # Attempt to extract primary/accent from section 2 YAML parsed_data
    color_section = next((s for s in sections if s.section_number == 2), None)
    colors: dict[str, str] = {}
    if color_section and color_section.parsed_data:
        for key, val in color_section.parsed_data.items():
            if isinstance(val, str) and re.match(r"^#[0-9a-fA-F]{3,6}$", val.strip()):
                colors[key] = val.strip()

    # Ensure required color keys exist (fallback to sensible defaults)
    if "primary" not in colors and colors:
        first_color = next(iter(colors.values()))
        colors["primary"] = first_color
    if "background" not in colors:
        colors["background"] = "#ffffff"
    if "text" not in colors:
        colors["text"] = colors.get("primary", "#000000")

    # Typography from section 3
    typo_section = next((s for s in sections if s.section_number == 3), None)
    typography: dict[str, str] = {}
    if typo_section and typo_section.parsed_data:
        if "heading_font" in typo_section.parsed_data:
            typography["heading_font"] = str(typo_section.parsed_data["heading_font"])
        if "body_font" in typo_section.parsed_data:
            typography["body_font"] = str(typo_section.parsed_data["body_font"])
    if "heading_font" not in typography:
        typography["heading_font"] = "sans-serif"
    if "body_font" not in typography:
        typography["body_font"] = "sans-serif"

    return {
        "id": theme_id,
        "name": name,
        "description": "",
        "version": "1.0.0",
        "author": "awesome-design-md",
        "source_url": AWESOME_REPO,
        "categories": [],
        "colors": colors,
        "typography": typography,
        "is_builtin": False,
    }


# ---------------------------------------------------------------------------
# Main import logic
# ---------------------------------------------------------------------------

def _update_registry(registry_path: Path, new_entry: dict) -> None:
    """Append or replace an entry in registry.json by id."""
    entries: list[dict] = []
    if registry_path.exists():
        entries = json.loads(registry_path.read_text(encoding="utf-8"))

    # Replace existing entry or append
    existing_ids = [e["id"] for e in entries]
    if new_entry["id"] in existing_ids:
        idx = existing_ids.index(new_entry["id"])
        entries[idx] = new_entry
    else:
        entries.append(new_entry)

    registry_path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_import(
    *,
    dry_run: bool = False,
    limit: int | None = None,
    output_dir: Path,
    repo_url: str = AWESOME_REPO,
) -> int:
    """
    Core import routine.

    Returns the number of themes successfully imported.
    """
    registry_path = output_dir / REGISTRY_FILENAME

    local_path = Path(repo_url).expanduser()
    if local_path.is_dir():
        # Local directory — use directly without cloning
        _log.info("Using local directory: %s", local_path)
        design_files = _discover_themes(local_path)
        _log.info("Discovered %d DESIGN.md files", len(design_files))
        return _do_import(
            design_files=design_files,
            output_dir=output_dir,
            registry_path=registry_path,
            dry_run=dry_run,
            limit=limit,
        )

    with tempfile.TemporaryDirectory(prefix="aio-import-") as tmpdir:
        clone_dir = Path(tmpdir) / "awesome-design-md"
        try:
            _clone_or_pull(repo_url, clone_dir)
        except subprocess.CalledProcessError as exc:
            _log.error("Failed to clone/pull repo: %s", exc)
            return 0

        design_files = _discover_themes(clone_dir)
        _log.info("Discovered %d DESIGN.md files", len(design_files))
        return _do_import(
            design_files=design_files,
            output_dir=output_dir,
            registry_path=registry_path,
            dry_run=dry_run,
            limit=limit,
        )


def _do_import(
    *,
    design_files: list[Path],
    output_dir: Path,
    registry_path: Path,
    dry_run: bool,
    limit: int | None,
) -> int:
    if limit is not None:
        design_files = design_files[:limit]

    imported = 0
    skipped = 0

    for design_path in design_files:
        text = design_path.read_text(encoding="utf-8", errors="replace")
        try:
            sections = parse_design_md(text)
        except (DesignSectionParseError, DesignSectionValidationError) as exc:
            _log.warning("Skipping %s: %s", design_path.parent.name, exc)
            skipped += 1
            continue

        meta = _extract_meta(design_path, sections)
        theme_id = meta["id"]
        theme_dir = output_dir / theme_id

        _log.info("  ✓ %s (%s)", meta["name"], theme_id)

        if not dry_run:
            theme_dir.mkdir(parents=True, exist_ok=True)

            # Copy DESIGN.md
            shutil.copy2(design_path, theme_dir / "DESIGN.md")

            # Generate theme.css from color + typography sections
            css_vars = extract_css_vars(sections)
            (theme_dir / "theme.css").write_text(css_vars or "/* no CSS vars extracted */\n", encoding="utf-8")

            # Generate layout.css stubs
            layout_css = extract_layout_css(sections)
            (theme_dir / "layout.css").write_text(layout_css or "/* no layout CSS extracted */\n", encoding="utf-8")

            # Write meta.json
            (theme_dir / "meta.json").write_text(
                json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            # Update registry
            _update_registry(registry_path, meta)

        imported += 1

    _log.info(
        "%s %d theme(s) from awesome-design-md (%d skipped)",
        "Would import" if dry_run else "Imported",
        imported,
        skipped,
    )
    return imported


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import themes from awesome-design-md into src/aio/themes/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true", help="Discover and validate without writing files")
    parser.add_argument("--limit", type=int, default=None, metavar="N", help="Import at most N themes")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / "src" / "aio" / "themes",
        metavar="DIR",
        help="Theme output directory (default: src/aio/themes/)",
    )
    parser.add_argument("--repo", default=AWESOME_REPO, metavar="URL", help=f"Source repo URL (default: {AWESOME_REPO})")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    count = run_import(
        dry_run=args.dry_run,
        limit=args.limit,
        output_dir=args.output,
        repo_url=args.repo,
    )
    if count == 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
