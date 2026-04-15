# Quick Start: Create Your First Presentation

This guide walks you through creating and customizing your first presentation with AIO — from setup to deployment. **Time: ~15 minutes.**

---

## Prerequisites

- Python 3.12+
- Basic Markdown knowledge
- Text editor (VS Code, Vim, etc.)

---

## Step 1: Install AIO (2 min)

### Option A: Development Setup

```bash
git clone https://github.com/renatobardi/aio.git
cd aio
pip install -e ".[dev]"
pip install -e ".[enrich]"  # for image generation + extraction

# Verify installation
aio --version
```

### Option B: Use AIO

```bash
pip install aio

# Verify installation
aio --version
```

---

## Step 2: Initialize Your First Project (1 min)

```bash
# Create a new presentation
aio init my-first-deck --theme minimal

# This creates:
cd my-first-deck
ls -la
# Output:
# .aio/
# └── config.yaml          # Project settings
# └── meta.json            # Metadata
# └── cache/               # Auto-created for images
# slides.md                # Your content file
```

**What's in `.aio/config.yaml`?**

```yaml
theme: minimal
output: out.html
cache_size_mb: 100
```

---

## Step 3: Write Your First Slides (5 min)

Edit `slides.md` with your favorite editor:

```bash
cat > slides.md << 'EOF'
---
title: "My First AIO Presentation"
subtitle: "Built in 15 minutes"
theme: minimal
---

# Slide 1: Welcome

Welcome to **AIO** — AI-native presentation generator.

This is a simple text slide with markdown formatting:
- Bullet point 1
- Bullet point 2
- **Bold text**
- *Italic text*

---

# Slide 2: Features

- 🚀 Zero external dependencies
- 📊 Built-in charts and icons
- 🎨 57+ design themes
- 🖼️ AI image generation

---

# Slide 3: Quick Stats

@chart-type: bar
@chart-data:
  labels: [Q1, Q2, Q3, Q4]
  series:
    - name: "2024 Revenue"
      values: [12000, 19000, 8000, 15000]
  title: "Quarterly Revenue"

---

# Slide 4: With Icons

Pick your favorite icons from 159 Lucide icons:

- @check-circle Success
- @trending-up Growth
- @lock Security
- @zap Performance

---

# Slide 5: Two-Column Layout

Left content here:
- Point A
- Point B

| Right | Content |
|-------|---------|
| Cell  | Data    |

---

# Slide 6: Code Block

```python
def greet(name):
    return f"Hello, {name}!"

print(greet("AIO"))
```

---

# Slide 7: Closing

Thank you! Questions?

**Links:**
- GitHub: https://github.com/renatobardi/aio
- Docs: https://aio-presentations.io
EOF
```

---

## Step 4: Build Your Presentation (< 5s)

### Simple Build (Fast)

```bash
aio build slides.md -o out.html

# Output:
# ✓ Parsed 7 slides
# ✓ Analyzed layouts
# ✓ Composed slides with charts
# ✓ Rendered Reveal.js HTML
# ✓ Inlined assets (no external URLs)
# → out.html (245 KB)
```

### Build with Live Preview

```bash
# Opens http://localhost:3000 automatically
# Changes to slides.md auto-reload in browser
aio serve slides.md --port 3000

# Press Ctrl+C to stop
```

### Build with AI Image Generation (optional)

```bash
# First build: generates images (~30s)
# Second+ builds: uses cache (~2s)
aio build slides.md --enrich -o out.html

# Check cache stats
aio build slides.md --cache-stats

# Output:
# Entries: 7
# Size: 3.2 MB / 100.0 MB
# AIO version: 0.1.0
```

---

## Step 5: Preview Your Presentation

### Open in Browser

```bash
# On macOS
open out.html

# On Linux
firefox out.html

# On Windows
start out.html
```

**Navigate:**
- **Arrow keys** — next/previous slide
- **ESC** — slide overview
- **S** — speaker notes (if added)
- **F** — fullscreen

---

## Step 6: Customize with a Theme (2 min)

### Browse Available Themes

```bash
# List all 57 themes
aio theme list

# See theme details
aio theme info linear

# Output:
# Theme: linear
# Category: Tech/SaaS
# Colors: 5 colors, WCAG AA compliant
# Author: linear.app
```

### Use a Different Theme

```bash
# Edit .aio/config.yaml
aio build slides.md --theme linear -o out.html

# Or use any of these:
aio build slides.md --theme stripe -o out.html
aio build slides.md --theme notion -o out.html
aio build slides.md --theme vibrant -o out.html
aio build slides.md --theme figma -o out.html
```

---

## Step 7: Add Images (Optional)

### Method A: AI Image Generation (Easiest)

```bash
# Add image hints to slides.md
---

# Slide: Hero with Generated Image

A beautiful tech conference with attendees.

---
```

```bash
# Build with --enrich flag
aio build slides.md --enrich -o out.html

# AIO automatically:
# 1. Extracts descriptions from slides
# 2. Generates images using Pollinations.ai (free)
# 3. Caches them in .aio/cache/images/
# 4. Embeds in HTML as base64
```

### Method B: Free Image Search

```bash
# Build from images using Unsplash
aio build slides.md --enrich --image-provider unsplash -o out.html

# Requires: export UNSPLASH_API_KEY=your_key
# Free tier: 50 requests/hour
```

### Method C: Paid Image Generation

```bash
# Use OpenAI DALL-E 3
aio build slides.md --enrich --image-provider openai -o out.html

# Requires: export OPENAI_API_KEY=your_key
# Cost: ~$0.08 per image
```

---

## Step 8: Add Charts & Data

### Simple Bar Chart

```markdown
# Revenue by Quarter

@chart-type: bar
@chart-data:
  labels: [Q1, Q2, Q3, Q4]
  series:
    - name: "Sales"
      values: [12000, 19000, 8000, 15000]
```

### Line Chart (Trends)

```markdown
# Growth Over Time

@chart-type: line
@chart-data:
  labels: [Jan, Feb, Mar, Apr, May, Jun]
  series:
    - name: "Users"
      values: [100, 150, 200, 280, 350, 420]
    - name: "MRR"
      values: [5000, 7500, 10000, 14000, 17500, 21000]
```

### Pie Chart (Distribution)

```markdown
# Market Share

@chart-type: pie
@chart-data:
  labels: [Product A, Product B, Product C]
  values: [45, 30, 25]
```

### Scatter Plot

```markdown
# Performance vs Cost

@chart-type: scatter
@chart-data:
  series:
    - name: "Options"
      points: [[10, 5], [20, 15], [30, 25]]
```

### Heatmap

```markdown
# Engagement by Day/Hour

@chart-type: heatmap
@chart-data:
  rows: [Mon, Tue, Wed, Thu, Fri]
  cols: [9am, 12pm, 3pm, 6pm]
  values: [[5, 10, 8, 3], [12, 15, 9, 4], ...]
```

---

## Step 9: Customize Further

### Add Speaker Notes

```markdown
---
speaker_notes: |
  This is my speaker notes.
  It won't appear in slides but will in speaker view (press 'S').
---

# Slide Title

Public content here.
```

### Set Layout Hints

```markdown
---
layout: hero
---

# Big Title

Full-screen centered layout.

---

---
layout: two-column
---

# Left Heading | Right Heading

Left content | Right content
```

### Add Metadata

```markdown
---
title: "My Presentation"
subtitle: "A subtitle"
author: "Your Name"
date: "2024-04-15"
theme: "linear"
---

# Slide 1

Content...
```

---

## Step 10: Export & Share

### Share Locally

```bash
# After building, share out.html:
# - Via email
# - On USB drive
# - Over HTTP (simple server)

python -m http.server 8000
# Opens: http://localhost:8000/out.html
```

### Deploy Online

```bash
# Option A: GitHub Pages
git init my-presentation
echo "out.html" >> .gitignore
git add slides.md
git commit -m "init"
git push origin main

# Then enable GitHub Pages in settings

# Option B: Netlify
netlify deploy --prod --dir=.

# Option C: Any static host (Vercel, Cloudflare, etc.)
# Just upload out.html
```

---

## Common Patterns

### Example: Product Pitch

```markdown
---
title: "My Startup Pitch"
theme: "stripe"
---

# 🚀 Our Problem

Market needs this.

---

# 💡 Our Solution

We built this.

---

# 📊 Traction

@chart-type: line
@chart-data:
  labels: [Month 1, Month 2, Month 3]
  series:
    - name: "Users"
      values: [100, 500, 2000]

---

# 💰 Ask

We're raising $1M.

---

# 👥 Team

Meet our founders.
```

### Example: Conference Talk

```markdown
---
title: "Building with AI"
subtitle: "A Deep Dive"
theme: "linear"
---

# Agenda

1. Context
2. Architecture
3. Lessons Learned
4. Q&A

---

# Chapter 1: Context

...
```

---

## Troubleshooting

### Build Fails: "No slides found"

```bash
# Check frontmatter syntax
# Make sure YAML is valid:
---
title: "My Title"
subtitle: "My Subtitle"
---

# NOT valid:
---
title: My Title  # Missing quotes
subtitle: My Subtitle
---
```

### Chart Doesn't Render

```bash
# Check @chart-data syntax
# Must be valid YAML with proper indentation:

@chart-type: bar
@chart-data:
  labels: [A, B, C]           # ✓ List syntax
  series:
    - name: "Series 1"
      values: [1, 2, 3]       # ✓ Indented 6 spaces
```

### Images Taking Too Long

```bash
# First build with --enrich is slow (generating images)
# Subsequent builds use cache:

# First: ~30s
aio build slides.md --enrich -o out.html

# Second: ~2s (cached)
aio build slides.md --enrich -o out.html

# Check cache
aio build slides.md --cache-stats

# Clear cache if needed
aio build slides.md --cache-clear --enrich -o out.html
```

### Theme Looks Wrong

```bash
# Validate theme compliance
aio theme validate linear

# Use a different theme
aio build slides.md --theme minimal -o out.html

# List all available themes
aio theme list
```

---

## Next Steps

1. **Read the docs**
   - [Architecture Overview](architecture-overview.md) — understand how AIO works
   - [Image Generation Guide](image-generation-troubleshooting.md) — debug image issues
   - [Theme Creation](theme-section-10-guide.md) — create custom themes

2. **Explore themes**
   - Try different themes: `aio theme list`
   - Pick one you love: `aio build slides.md --theme stripe`

3. **Add your content**
   - Replace sample slides with your own
   - Use charts for data
   - Generate images with `--enrich`

4. **Contribute**
   - Have ideas? [Open an issue](https://github.com/renatobardi/aio/issues)
   - Want to contribute? [See CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Tips & Tricks

- **Hot reload**: Use `aio serve` instead of rebuilding manually
- **Cache images**: `aio build --enrich` caches across rebuilds for 95% faster iterations
- **Layout hints**: Use `@layout: hero` or `@layout: two-column` for exact control
- **Keyboard shortcuts**: Press **?** in slide viewer for all shortcuts
- **Speaker view**: Press **S** during presentation for notes + timer
- **Export to PDF**: Most browsers: Print → Save as PDF

---

## Support

- **Questions**: Check [FAQ](faq.md)
- **Issues**: [GitHub Issues](https://github.com/renatobardi/aio/issues)
- **Docs**: [Full documentation](../README.md)
