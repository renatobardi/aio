# UX Checklist — 002-core-layouts-theme-system

## Layout Rendering

- [ ] hero-title renders with large, centered heading (≥ 48px equivalent)
- [ ] stat-highlight renders stat number prominently (≥ 64px, theme accent color)
- [ ] split-image-text renders true 50/50 grid with image on left
- [ ] comparison-2col renders two clearly distinguishable columns
- [ ] quote renders blockquote with left border accent and italic text
- [ ] key-takeaways renders each bullet with ✓ checkmark glyph
- [ ] closing renders CTA in a prominent, visually distinct block
- [ ] content-with-icons renders 3-column icon+title+description grid

## Theme UX

- [ ] `aio theme list` table has readable column alignment and fits standard terminal width (80+)
- [ ] `aio theme info` output is scannable (labels left-aligned, values right-aligned or distinct)
- [ ] `aio theme use` confirmation message is clear and actionable
- [ ] `aio theme create` success message tells user what to do next (edit DESIGN.md)

## CLI Error Messages

- [ ] Unknown layout → warns but doesn't crash; user sees which layout was unknown
- [ ] Missing image file → warns with path; placeholder shown in output
- [ ] Unknown theme → clear error with suggestion to run `aio theme list`
- [ ] Port collision → message names the port and suggests an alternative (`--port 8001`)
- [ ] `aio theme use` outside project → message explains how to init a project

## Build Feedback

- [ ] Build progress shows step numbers (Step 1/5, 2/5, etc.)
- [ ] Final success message includes output file path and size
- [ ] `--dry-run` output is visually distinct from real build (e.g., `[dry-run]` prefix)
