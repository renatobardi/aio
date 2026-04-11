---
title: Quick Start
agent: claude
theme: minimal
---

# Welcome to AIO

<!-- @layout: hero-title -->
<!-- @title: Welcome to AIO -->
<!-- @subtitle: AI-native presentation generator -->

AIO turns your Markdown into beautiful, self-contained HTML presentations.

---

# What is AIO?

<!-- @layout: content -->

AIO is a command-line tool that:

- Converts `slides.md` into a single offline HTML file
- Supports 16+ slide layouts (hero, content, two-column, code, quote...)
- Works with 8 AI agents (Claude, Gemini, ChatGPT, Copilot...)
- Ships with 64+ visual themes from awesome-design-md

No internet required at presentation time — everything is embedded.

---

# Getting Started

<!-- @layout: two-column -->
<!-- @title: Three Simple Commands -->

**Left column**: Initialize

```bash
aio init my-deck \
  --agent claude \
  --theme minimal
```

**Right column**: Build & Serve

```bash
aio build slides.md
aio serve slides.md
```

---

# "AIO changed how I present."

<!-- @layout: quote -->
<!-- @quote: AIO changed how I present. I type Markdown, Claude enriches it, and I have a stunning deck in minutes. -->
<!-- @attribution: Early Adopter, 2026 -->

---

# Next Steps

<!-- @layout: content -->
<!-- @icon: arrow-right -->

Ready to build your first deck?

1. Run `aio init my-deck --agent claude --theme minimal`
2. Edit `slides.md` with your content
3. Run `aio build slides.md` to generate HTML
4. Run `aio serve slides.md` for live preview

**Resources**: `aio --help` · `aio theme list` · `aio commands list`
