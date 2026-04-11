# CLI Contract: M1 Additions and Changes

**Spec**: AIO Core Layouts & Theme System (M1)
**Base contract**: `specs/main/contracts/cli-contract.md`
**Scope**: New commands and changes to existing commands in M1 only.

---

## `aio theme list` (updated)

**Signature**: `aio theme list [--limit N] [--filter TAGS] [--search QUERY] [--json]`

**Arguments/Options**:
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--limit N` | int | 20 | Max number of themes to display |
| `--filter TAGS` | str | None | Comma-separated tag filter (e.g. `design-system,dark`) |
| `--search QUERY` | str | None | Fuzzy search on theme name, id, and categories (difflib) |
| `--json` | flag | False | Emit JSON array instead of Rich table |

**Exit codes**:
| Code | Condition |
|------|-----------|
| 0 | Themes listed successfully (even if 0 results) |
| 1 | Registry file not found or malformed |

**Stdout**: Rich table with columns: ID, Name, Tags, Source, Description (truncated at 60 chars). With `--json`: JSON array of theme objects.

**Stderr**: `[INFO] Loaded N themes from registry` on success.

**Example**:
```shell
$ aio theme list --filter dark --limit 3
┌─────────────────┬──────────────────┬──────────────┬──────────┬─────────────────────────────┐
│ ID              │ Name             │ Tags         │ Source   │ Description                 │
├─────────────────┼──────────────────┼──────────────┼──────────┼─────────────────────────────┤
│ stripe-checkout │ Stripe Checkout  │ dark,minimal │ imported │ Clean dark checkout flow... │
│ linear-app      │ Linear App       │ dark,product │ imported │ Dense data-rich dark UI...  │
│ vercel-dash     │ Vercel Dashboard │ dark,saas    │ imported │ Monochrome dashboard...     │
└─────────────────┴──────────────────┴──────────────┴──────────┴─────────────────────────────┘
Showing 3 of 14 matching themes.
```

---

## `aio theme search` (new)

**Signature**: `aio theme search QUERY [--limit N] [--json]`

**Arguments/Options**:
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `QUERY` | str | required | Search string matched against name, id, categories |
| `--limit N` | int | 10 | Max results |
| `--json` | flag | False | Emit JSON array |

**Exit codes**:
| Code | Condition |
|------|-----------|
| 0 | Search completed (even if 0 results) |
| 1 | Registry not found or malformed |

**Stdout**: Rich table identical to `theme list` with an additional `Score` column (0.0–1.0, two decimal places). Sorted descending by score.

**Stderr**: `[INFO] Searched N themes, found M matches`.

**Example**:
```shell
$ aio theme search "dark minimal saas"
┌─────────────┬──────────────┬──────────────┬───────┐
│ ID          │ Name         │ Tags         │ Score │
├─────────────┼──────────────┼──────────────┼───────┤
│ linear-app  │ Linear App   │ dark,minimal │  0.91 │
│ vercel-dash │ Vercel Dash  │ dark,saas    │  0.78 │
└─────────────┴──────────────┴──────────────┴───────┘
```

---

## `aio theme info` (new)

**Signature**: `aio theme info ID [--json]`

**Arguments/Options**:
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `ID` | str | required | Theme identifier (exact match) |
| `--json` | flag | False | Emit JSON object instead of Rich panel |

**Exit codes**:
| Code | Condition |
|------|-----------|
| 0 | Theme found and info displayed |
| 2 | Theme ID not found in any registry |

**Stdout**: Rich panel containing: name, id, source, tags, color palette (hex), typography summary, and Agent Prompt Snippet (DESIGN.md section 11, truncated at 300 chars). With `--json`: valid JSON object with keys `id`, `name`, `author`, `categories`, `colors`, `typography`.

**Stderr**: `[INFO] Displaying info for theme {ID}`.

**Example**:
```shell
$ aio theme info linear-app
╭─ Linear App ────────────────────────────────────────────────────╮
│ ID:         linear-app                                          │
│ Source:     imported (awesome-design-md)                        │
│ Tags:       dark, minimal, product, data-dense                  │
│ Palette:    #0F0F0F #5E6AD2 #FFFFFF #1A1A1A                    │
│ Typography: Inter 14/16/24px, monospace code                   │
│ Prompt:     Dense dark UI with indigo accents. Favor ...        │
╰─────────────────────────────────────────────────────────────────╯
```

---

## `aio theme use` (new)

**Signature**: `aio theme use ID [--project-dir DIR]`

**Arguments/Options**:
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `ID` | str | required | Theme identifier to activate |
| `--project-dir DIR` | path | `.` (cwd) | Target project directory (must contain `.aio/`) |

**Exit codes**:
| Code | Condition |
|------|-----------|
| 0 | Theme installed and config updated |
| 2 | Theme ID not found in registry |
| 3 | Target directory has no `.aio/` config dir (not an AIO project) |

**Stdout**: `Theme 'linear-app' activated. Rebuild with: aio build slides.md`

**Stderr**: `[INFO] Copying theme files to .aio/themes/linear-app/`; `[INFO] Updated .aio/config.yaml theme: linear-app`.

**Side effects**: Copies theme directory to `.aio/themes/{ID}/`. Updates `theme:` key in `.aio/config.yaml`. Does NOT trigger a rebuild.

**Example**:
```shell
$ aio theme use linear-app
Theme 'linear-app' activated. Rebuild with: aio build slides.md
```

---

## `aio theme show` (new)

**Signature**: `aio theme show ID [--section N] [--raw]`

**Arguments/Options**:
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `ID` | str | required | Theme identifier |
| `--section N` | int | None | Show only section N (1–11). Omit for full document. |
| `--raw` | flag | False | Print raw Markdown instead of Rich-rendered output |

**Exit codes**:
| Code | Condition |
|------|-----------|
| 0 | DESIGN.md displayed |
| 2 | Theme ID not found |
| 3 | `--section N` out of range (not 1–11) |
| 4 | Theme has no DESIGN.md |

**Stdout**: Rich Markdown-rendered DESIGN.md (or raw text with `--raw`).

**Stderr**: `[INFO] Showing DESIGN.md for theme {ID}`.

**Example**:
```shell
$ aio theme show linear-app --section 2
## 2. Color Palette

| Role       | Hex     | Usage              |
|------------|---------|--------------------|
| Background | #0F0F0F | Page background    |
| Primary    | #5E6AD2 | Links, CTAs        |
| Surface    | #1A1A1A | Cards, panels      |
| Text       | #FFFFFF | Body text          |
```

---

## `aio theme create` (new)

**Signature**: `aio theme create NAME [--from ID] [--edit]`

**Arguments/Options**:
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `NAME` | str | required | New theme identifier (slug: lowercase, hyphens only) |
| `--from ID` | str | None | Base on existing theme (copies and renames). Omit for blank scaffold. |
| `--edit` | flag | False | Open DESIGN.md in `$EDITOR` after creation |

**Exit codes**:
| Code | Condition |
|------|-----------|
| 0 | Theme scaffold created |
| 2 | `--from ID` not found in registry |
| 3 | Theme with NAME already exists in `.aio/themes/` |
| 4 | NAME contains invalid characters (not `[a-z0-9-]`) |

**Stdout**:
```
Created theme 'my-brand' at .aio/themes/my-brand/
  DESIGN.md       ← fill in all 11 sections
  theme.css       ← base styles
  layout.css      ← reveal.js layout overrides
  meta.json       ← name, tags, description
Validate with: aio theme validate my-brand
```

**Stderr**: `[INFO] Scaffolded theme my-brand from template`.

**Example**:
```shell
$ aio theme create my-brand --from linear-app
Created theme 'my-brand' at .aio/themes/my-brand/
  DESIGN.md
  theme.css
  layout.css
  meta.json
Validate with: aio theme validate my-brand
```

---

## `aio build` (updated — 5-step pipeline)

**Signature**: `aio build SOURCE [--output PATH] [--theme ID] [--enrich] [--provider NAME] [--dry-run]`

**Arguments/Options**:
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `SOURCE` | path | `slides.md` | Input Markdown file |
| `--output PATH` | path | `build/slides.html` | Output HTML file path |
| `--theme ID` | str | from `.aio/config.yaml` | Override active theme |
| `--enrich` | flag | False | Enable image generation via Pollinations.ai |
| `--provider NAME` | str | `pollinations` | Image generation provider |
| `--dry-run` | flag | False | Run all 5 steps but do not write output file |

**Exit codes**:
| Code | Condition |
|------|-----------|
| 0 | Build succeeded; output file written |
| 1 | Source file not found or unreadable |
| 2 | Theme not found or invalid (fails validation) |
| 3 | External URL detected in output HTML (Art. II violation) |
| 4 | YAML frontmatter parse error |
| 5 | Jinja2 template render error |

**Stdout**: Path + stats on success: `Built: out.html (42 slides, 1.2 MB)`. With `--dry-run`: `[dry-run] Would write 1.2 MB to out.html`.

**Stderr** (structured, one line per step):
```
[INFO]  PARSE   slides.md → 42 slides (0.12s)
[INFO]  ANALYZE 42 slides → layouts inferred (0.03s)
[INFO]  COMPOSE 42 slides → HTML fragments (1.8s)
[INFO]  RENDER  42 slides → Jinja2 rendered (0.4s)
[INFO]  INLINE  assets embedded, 0 external URLs (0.9s)
[INFO]  Build complete: out.html (1.2 MB) in 3.3s
```

**Unknown layout fallback**: WARNING logged naming the unknown layout; slide falls back to `content` layout; build continues and exits 0.

**Example**:
```shell
$ aio build slides.md -o out.html --theme linear-app
[INFO]  PARSE   slides.md → 30 slides (0.09s)
[INFO]  ANALYZE 30 slides → layouts inferred (0.02s)
[INFO]  COMPOSE 30 slides → HTML fragments (1.1s)
[INFO]  RENDER  30 slides → Jinja2 rendered (0.3s)
[INFO]  INLINE  assets embedded, 0 external URLs (0.6s)
Built: out.html (30 slides, 0.9 MB)
```

---

## `aio serve` (updated — Starlette ASGI + SSE hot reload)

**Signature**: `aio serve SOURCE [--port N] [--host ADDR] [--open]`

**Arguments/Options**:
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `SOURCE` | path | `slides.md` | Input Markdown file to watch and serve |
| `--port N` | int | 3000 | TCP port to listen on |
| `--host ADDR` | str | `127.0.0.1` | Bind address. Use `0.0.0.0` for LAN access. |
| `--open` | flag | False | Open browser tab after server starts |

**Exit codes**:
| Code | Condition |
|------|-----------|
| 0 | Server shut down cleanly (SIGINT / Ctrl-C) |
| 1 | Source file not found |
| 2 | Port already in use |
| 3 | Initial build failed (surface build exit code) |

**Stdout**: None (server runs until interrupted).

**Stderr**:
```
[INFO]  Serving slides.md on http://127.0.0.1:3000
[INFO]  SSE hot-reload active on http://127.0.0.1:3000/__sse__
[INFO]  Watching: /abs/path/to/slides.md
[INFO]  slides.md changed — rebuilding...
[INFO]  Rebuild complete (1.1s) — reload pushed to 1 client(s)
[INFO]  Shutting down...
```

**Routes**:
| Route | Method | Content-Type | Response |
|-------|--------|-------------|---------|
| `/` | GET | `text/html` | Latest built presentation with injected SSE client |
| `/__sse__` | GET | `text/event-stream` | SSE stream |

**SSE events**:
| Event data | When |
|------------|------|
| `{"type":"connected","message":"SSE connected"}` | Client opens SSE connection |
| `{"type":"reload","message":"File changed: slides.md"}` | Source file changed and rebuild succeeded |
| `{"type":"error","message":"<build stderr last line>"}` | Rebuild failed |

**Injected JS** (stripped from `aio build` output; present only in serve mode):
```html
<script>const es=new EventSource('\/__sse__');es.onmessage=()=>location.reload()<\/script>
```

**Note**: The `</script>` escape is `<\/script>` per Art. VIII (Reveal.js 5.x Jinja2 rule). The SSE client uses `EventSource`, not WebSocket.

**Example**:
```shell
$ aio serve slides.md --port 3000
[INFO]  Serving slides.md on http://127.0.0.1:3000
[INFO]  SSE hot-reload active on http://127.0.0.1:3000/__sse__
^C
[INFO]  Shutting down...
```
