# Minimal Theme — DESIGN.md

## Visual Theme

Clean, distraction-free aesthetic for technical and professional presentations.
Inspiration: Swiss typographic style, editorial design. Target audience: developers,
architects, engineers who want substance over decoration.

## Color Palette

- Primary: `#1a1a1a` — headings, key text
- Secondary: `#4a4a4a` — body text
- Accent: `#0066cc` — links, highlights, CTAs
- Background: `#ffffff` — slide background
- Surface: `#f5f5f5` — code blocks, callouts
- Danger: `#cc0000` — errors, warnings
- Contrast ratios: Primary on Background = 16.1:1 (AAA); Secondary = 9.4:1 (AAA)

## Typography

- Heading font: Inter, system-ui, sans-serif
- Body font: Inter, system-ui, sans-serif
- Code font: JetBrains Mono, monospace
- H1: 3rem / 1.1 line-height / 700 weight
- H2: 2rem / 1.2 line-height / 600 weight
- Body: 1.125rem / 1.6 line-height / 400 weight
- Code: 0.875rem / 1.5 line-height / 400 weight

## Components

**Buttons**: Flat, no shadow. Primary: `#0066cc` bg / white text. Secondary: `#f5f5f5` bg / `#1a1a1a` text.
**Badges**: Inline, `0.75rem`, rounded-sm, `#f5f5f5` bg.
**Cards**: White bg, 1px `#e0e0e0` border, `0.5rem` radius, `1.5rem` padding.
**Callouts**: Left border `4px #0066cc`, `#f0f7ff` bg, `1rem` padding.
**Code blocks**: `#f5f5f5` bg, `0.25rem` radius, Pygments syntax highlighting.

## Layout System

- Grid: 12-column, `1.5rem` gutter
- Spacing scale: 0.25 / 0.5 / 1 / 1.5 / 2 / 3 / 4 / 6rem
- Slide safe area: 3rem horizontal, 2.5rem vertical padding
- Max content width: 56rem (896px)
- Breakpoints: mobile < 640px, tablet < 1024px, desktop ≥ 1024px

## Depth & Shadows

- Level 0 (flat): no shadow
- Level 1 (card): `0 1px 3px rgba(0,0,0,0.08)`
- Level 2 (modal): `0 4px 12px rgba(0,0,0,0.12)`
- Level 3 (overlay): `0 8px 24px rgba(0,0,0,0.16)`
- Level 4 (toast): `0 16px 40px rgba(0,0,0,0.20)`

## Do's & Don'ts

**Do:**
- Use generous whitespace between slide elements
- Limit each slide to one primary idea
- Use monochrome imagery or high-contrast photos
- Align content to the grid baseline

**Don't:**
- Use more than 2 font sizes per slide
- Use decorative or rounded fonts
- Apply background textures or gradients
- Crowd content — prefer fewer words

## Responsive Behavior

- Mobile (< 640px): Single column, font sizes scale down 20%, padding halved
- Tablet (640–1024px): Reduced multi-column; H1 2.25rem
- Desktop (≥ 1024px): Full grid, standard sizing
- Two-column layouts stack on mobile
- Code blocks scroll horizontally on narrow viewports

## Animation & Transitions

- Default transition: fade, 300ms ease
- Slide transitions: fade-in 200ms
- No motion for users with `prefers-reduced-motion: reduce`
- List items: no animation in default mode (add via Reveal.js fragment class)
- Easing: `cubic-bezier(0.4, 0, 0.2, 1)` (Material Design standard)

## Accessibility

- WCAG 2.1 AA compliance for all color combinations
- All interactive elements have focus indicators (`2px #0066cc` outline)
- Images require `alt` text (enforced by DESIGN.md parser warning)
- Code examples use `<code>` semantic tags
- Slide sections use `<section>` with `aria-label`
- Minimum touch target: 44×44px
- Font size never below 0.875rem (14px)

## Agent Prompt Snippet

The **Minimal** theme uses a clean, high-contrast palette centered on `#1a1a1a` text
on white backgrounds. Typography is Inter at 3rem H1 / 2rem H2 / 1.125rem body.
Layout follows a 12-column grid with 3rem horizontal safe areas.

When generating slides for this theme: use short, punchy headings; keep body text under
40 words per slide; prefer `hero-title` for openers, `content` for details, `code` for
technical examples. Avoid decorative elements — the Minimal theme is substance-first.
Color accent (`#0066cc`) should appear on 1–2 elements per slide maximum.
