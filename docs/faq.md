# Frequently Asked Questions (FAQ)

---

## General Questions

### Q: What is AIO?

**A:** AIO is an **AI-native CLI toolkit** that converts Markdown files into fully self-contained, offline-capable HTML presentations. It's powered by Reveal.js 5.x and includes automatic layout inference, SVG charts, icons, and optional AI image generation.

**Key features:**
- Single `.html` output file (zero external dependencies)
- Works offline anywhere
- 57+ design themes
- 5 chart types (Bar, Line, Pie, Scatter, Heatmap)
- 159 built-in icons
- Optional AI image generation

### Q: How does AIO differ from PowerPoint, Google Slides, Keynote?

**A:** 

| Feature | AIO | PowerPoint | Google Slides | Keynote |
|---------|-----|-----------|--------------|---------|
| **Offline** | ✅ Fully | ✅ Yes | ❌ No | ✅ Yes |
| **Format** | `.html` (text-based) | `.pptx` (binary) | `.gslides` (cloud) | `.key` (binary) |
| **Git-friendly** | ✅ Diffs work | ❌ Binary | ❌ Cloud | ❌ Binary |
| **Code in slides** | ✅ Yes | ⚠️ Limited | ⚠️ Limited | ⚠️ Limited |
| **Charts** | ✅ 5 types, pure SVG | ✅ Yes | ✅ Yes | ✅ Yes |
| **AI images** | ✅ Auto-generate | ❌ No | ❌ No | ❌ No |
| **Free themes** | ✅ 57+ | ⚠️ Limited | ✅ Some | ⚠️ Limited |

**Best for:** Developers, tech talks, product pitches, design systems, API documentation.

### Q: Do I need internet to use presentations created with AIO?

**A:** No. Output is a single `.html` file with **zero external dependencies**. It works completely offline.

Image generation happens at **build time** (with `--enrich`), then images are embedded as base64. The result can be opened on any device with no internet.

---

## Installation & Setup

### Q: What are the system requirements?

**A:** 
- **Python**: 3.12+ (primary), 3.10+ (tolerated but not guaranteed)
- **Disk**: 150 MB for core, 250 MB with `[enrich]`
- **OS**: macOS, Linux, Windows (via WSL or native)

### Q: Should I install from GitHub or pip?

**A:** 

**For development** (if you want to contribute):
```bash
git clone https://github.com/renatobardi/aio.git
cd aio
pip install -e ".[dev]"
pip install -e ".[enrich]"
```

**For everyday use**:
```bash
pip install aio
```

### Q: What's the difference between `.[dev]` and `.[enrich]`?

**A:**

| Install | Includes | Purpose |
|---------|----------|---------|
| `pip install aio` | Core only | Just use AIO |
| `.[dev]` | Core + pytest, ruff, mypy | Develop AIO itself |
| `.[enrich]` | Core + pillow, bs4, lxml, cssutils | Image generation + web scraping |

**Recommendation:** If you're starting, just use `pip install aio`. Add `[dev]` and `[enrich]` if you need image generation or want to contribute.

---

## Creating Presentations

### Q: What's the simplest way to create a presentation?

**A:** 

```bash
# 1. Initialize project
aio init my-deck --theme minimal

# 2. Edit slides.md with your content
nano my-deck/slides.md

# 3. Build
aio build my-deck/slides.md -o out.html

# 4. Open in browser
open out.html
```

👉 See [quickstart-first-presentation.md](quickstart-first-presentation.md) for a detailed walkthrough.

### Q: Can I use AIO without knowing Markdown?

**A:** Markdown is very simple. Here's all you need:

```markdown
# Heading

Paragraph text.

- Bullet point 1
- Bullet point 2

**Bold** and *italic*

| Table | Syntax |
|-------|--------|
| Works | Great  |
```

Most AIO presentations use just these basics. Learn Markdown in 5 minutes: https://commonmark.org/help/

### Q: How do I add a title slide?

**A:** 

```markdown
---
title: "My Presentation"
subtitle: "A subtitle"
theme: "minimal"
---

# First Slide

Content here...
```

The `---` block at the top is **frontmatter**. AIO creates a title slide automatically.

### Q: Can I use HTML directly in slides?

**A:** Yes, but **not recommended** for offline-first compliance. Stick to Markdown.

However, you can embed SVG directly:
```markdown
# Slide with SVG

<svg viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="40" fill="blue"/>
</svg>
```

---

## Themes

### Q: How do I choose a theme?

**A:** 

```bash
# Browse all 57 themes
aio theme list

# See theme details
aio theme info linear
aio theme info stripe
aio theme info notion

# Build with a specific theme
aio build slides.md --theme linear -o out.html
```

Try 2-3 themes and pick the one you like.

### Q: Can I create a custom theme?

**A:** Yes! Create a `DESIGN.md` with 11 sections:

1. Visual Theme
2. Color Palette
3. Typography
4. Components
5. Layout System
6. Depth & Shadows
7. Do's & Don'ts
8. Responsive Behavior
9. Animation & Transitions
10. Accessibility
11. Agent Prompt Snippet

👉 See [theme-section-10-guide.md](theme-section-10-guide.md) for detailed instructions.

### Q: Can I modify an existing theme?

**A:** Yes, but **don't edit the built-in theme files directly**. Instead:

1. Copy the theme: `cp -r src/aio/themes/linear my-theme`
2. Edit `my-theme/theme.css` or `my-theme/layout.css`
3. Use it: `aio build slides.md --theme my-theme`

### Q: Where are themes stored?

**A:** 

- **Built-in**: `src/aio/themes/{theme-id}/`
- **Per-project**: `.aio/themes/registry.json` (lists selected themes only)
- **Global registry**: `src/aio/themes/registry.json` (all 57+ themes)

---

## Charts & Data

### Q: How do I add a chart?

**A:** Use `@chart-type` and `@chart-data`:

```markdown
# Sales by Region

@chart-type: bar
@chart-data:
  labels: [North, South, East, West]
  series:
    - name: "2023"
      values: [100, 150, 120, 90]
    - name: "2024"
      values: [120, 180, 130, 110]
```

Supported types: `bar`, `line`, `pie`, `scatter`, `heatmap`.

### Q: Can I import chart data from a file?

**A:** Not yet, but you can paste CSV/JSON data:

```markdown
@chart-type: bar
@chart-data:
  labels: [Q1, Q2, Q3, Q4]
  values: [10, 20, 15, 25]
```

Workaround: Use Python to convert CSV to YAML:
```python
import csv, yaml
with open('data.csv') as f:
    reader = csv.DictReader(f)
    data = list(reader)
print(yaml.dump({'data': data}))
```

### Q: What if my data changes frequently?

**A:** Regenerate the presentation when data changes:

```bash
aio build slides.md --enrich -o out.html
```

AIO caches images, so rebuilds are fast (~2s).

---

## Images & Image Generation

### Q: How do I add images?

**A:** 

**Option A: Inline markdown**
```markdown
# My Slide

![Alt text](path/to/image.jpg)
```

**Option B: AI generate images**
```bash
aio build slides.md --enrich -o out.html
```

AIO extracts slide descriptions and generates images automatically.

### Q: What image providers does AIO support?

**A:**

| Provider | Cost | API Key | Speed | Quality |
|----------|------|---------|-------|---------|
| **Pollinations** (default) | Free | None | ~8s | Good |
| **DALL-E 3** (OpenAI) | ~$0.08/img | `OPENAI_API_KEY` | ~10s | Excellent |
| **Unsplash** | Free | `UNSPLASH_API_KEY` | ~5s | Great |
| **SVG fallback** | Free | None | <500ms | Basic |

Default is **Pollinations** (free, no API key). If it fails, AIO falls back to SVG.

### Q: How do I use a paid provider like DALL-E?

**A:**

```bash
# Set API key
export OPENAI_API_KEY=sk-xxx...

# Use DALL-E
aio build slides.md --enrich --image-provider openai -o out.html

# Estimate cost first (dry-run)
aio build slides.md --enrich --image-provider openai --dry-run
```

Cost: ~$0.08 per image × number of slides = $0.80–$3.00 per deck.

### Q: Can I cache images across builds?

**A:** Yes, automatically! AIO caches images in `.aio/cache/images/`:

```bash
# First build: generates images (~30s)
aio build slides.md --enrich -o out.html

# Second build: uses cache (~2s)
aio build slides.md --enrich -o out.html

# Check cache
aio build slides.md --cache-stats

# Clear cache
aio build slides.md --cache-clear
```

Cache is LRU (Least Recently Used) — when it exceeds 100 MB, oldest entries are deleted until < 50 MB.

### Q: How do I extract images from a design site?

**A:** Use `aio extract`:

```bash
aio extract https://stripe.com -o DESIGN.md

# This creates a 11-section DESIGN.md with:
# - Color palette
# - Typography
# - Components
# - All sections needed for a custom theme
```

Requires `pip install -e ".[enrich]"` (includes web scraping libraries).

---

## Performance & Optimization

### Q: How fast is AIO?

**A:**

| Operation | Time |
|-----------|------|
| Build 30 slides (no enrich) | < 5s |
| Serve hot-reload | < 2s |
| Parse 100 slides | < 500ms |
| Generate 1 image (Pollinations) | ~8s |
| Generate 1 image (cached) | ~0.1s |
| Full build with 30 images (first) | ~30s |
| Full build with 30 images (cached) | ~2s |

### Q: Why is my first build slow?

**A:** If using `--enrich`, AIO generates images:

```bash
aio build slides.md --enrich -o out.html
# First: ~30s (generating images)
# Second: ~2s (cached)
```

Without `--enrich`, builds are < 5s.

### Q: Can I skip enrichment for drafts?

**A:** Yes:

```bash
# Fast draft build (no images)
aio build slides.md -o out.html

# Later: add images
aio build slides.md --enrich -o out.html
```

---

## Deployment & Sharing

### Q: How do I share a presentation?

**A:** 

```bash
# Option 1: Email
# Attachment: out.html (single file, any size)

# Option 2: USB drive
cp out.html /Volumes/usb-drive/

# Option 3: Online
# GitHub Pages, Netlify, Vercel, AWS S3, etc.
# Just upload the .html file
```

Presentations work **offline and online** — no server required.

### Q: Can I deploy to GitHub Pages?

**A:**

```bash
# Create a repo
git init my-presentation
git add slides.md .aio/
git commit -m "Initial commit"
git remote add origin https://github.com/username/my-presentation.git
git push -u origin main

# In GitHub settings:
# - Enable Pages
# - Source: main branch
# - Custom domain (optional)

# Result: https://username.github.io/my-presentation/out.html
```

### Q: Can I use AIO with a custom domain?

**A:** Yes, deploy the `.html` file to any static host:

- **GitHub Pages**: Free, easy
- **Netlify**: Free with custom domain
- **Vercel**: Free with custom domain
- **CloudFlare Pages**: Free with custom domain
- **AWS S3**: ~$1/month
- **Your own server**: Any static file server

---

## Troubleshooting

### Q: Build fails with "yaml: line N: mapping values are not allowed here"

**A:** YAML syntax error in frontmatter. Common mistakes:

```markdown
# ❌ Wrong (missing quotes)
---
title: My Title
subtitle: My Subtitle
---

# ✅ Right (with quotes)
---
title: "My Title"
subtitle: "My Subtitle"
---
```

Check indentation — YAML is whitespace-sensitive.

### Q: "External URL found in output" error

**A:** AIO requires 100% offline output. You have an external URL:

```bash
aio build slides.md -o out.html
# ERROR: External URL found in output: https://example.com
```

Fix by removing external URLs or embedding assets:

```markdown
# ❌ Wrong
![](https://example.com/image.jpg)

# ✅ Right (local file)
![](./images/my-image.jpg)

# ✅ Right (with --enrich, AIO embeds)
aio build slides.md --enrich -o out.html
```

### Q: Image generation fails

**A:** See [image-generation-troubleshooting.md](image-generation-troubleshooting.md) for detailed debugging.

Quick checklist:
```bash
# Check internet connection
ping image.pollinations.ai

# Check API keys (if using OpenAI/Unsplash)
echo $OPENAI_API_KEY
echo $UNSPLASH_API_KEY

# Try fallback (SVG)
aio build slides.md -o out.html  # Without --enrich
```

### Q: Slide layout looks wrong

**A:**

```bash
# Validate theme
aio theme validate linear

# Try a different theme
aio build slides.md --theme minimal -o out.html

# Check if metadata is valid
grep "@" slides.md | head -5
```

### Q: "Theme not found" error

**A:**

```bash
# List available themes
aio theme list

# Use a valid theme name
aio build slides.md --theme linear -o out.html  # ✅
aio build slides.md --theme "linear" -o out.html  # ✅
aio build slides.md --theme my-custom-theme -o out.html  # ❌ if not found
```

---

## Contributing & Support

### Q: How do I report a bug?

**A:** 

1. Check [GitHub Issues](https://github.com/renatobardi/aio/issues) — someone might have reported it
2. Gather debug info:
   ```bash
   aio --version
   python --version
   aio build slides.md -v 2>&1 | tee debug.log
   ```
3. Open a new issue with:
   - Error message (full output)
   - Steps to reproduce
   - Your environment (OS, Python version)
   - Expected vs actual behavior

### Q: Can I contribute to AIO?

**A:** Yes! See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Setup instructions
- Branch naming conventions
- Code quality standards
- Testing requirements
- Git workflow

### Q: Where's the documentation?

**A:**

| Doc | Purpose |
|-----|---------|
| [README.md](../README.md) | Overview, quick start, common commands |
| [quickstart-first-presentation.md](quickstart-first-presentation.md) | Step-by-step guide (15 min) |
| [architecture-overview.md](architecture-overview.md) | How AIO works internally |
| [image-generation-troubleshooting.md](image-generation-troubleshooting.md) | Debug image issues |
| [theme-section-10-guide.md](theme-section-10-guide.md) | Create custom themes |
| [CLAUDE.md](../CLAUDE.md) | For AI code assistants |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | How to contribute |
| [specs/main/plan.md](../specs/main/plan.md) | Roadmap & architecture decisions |

---

## More Questions?

- **Check**: [GitHub Discussions](https://github.com/renatobardi/aio/discussions)
- **Report**: [GitHub Issues](https://github.com/renatobardi/aio/issues)
- **Contribute**: [CONTRIBUTING.md](../CONTRIBUTING.md)
