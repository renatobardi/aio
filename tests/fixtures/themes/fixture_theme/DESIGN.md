# Fixture Theme — DESIGN.md

## 1. Visual Theme

A minimal, clean theme designed for automated testing. Uses a simple blue-and-white palette with Inter as the sole typeface. Prioritizes legibility and contrast over decorative elements.

## 2. Color Palette

```yaml
primary: "#1a56db"
accent: "#e74694"
background: "#ffffff"
text: "#111827"
neutral: "#6b7280"
```

- Primary: #1a56db — used for headings and interactive elements
- Accent: #e74694 — used for highlights and call-to-action elements
- Background: #ffffff — slide background
- Text: #111827 — body text
- Neutral: #6b7280 — secondary labels and captions

## 3. Typography

```yaml
heading_font: "Inter"
body_font: "Inter"
sizes:
  h1: "3rem"
  h2: "2rem"
  h3: "1.5rem"
  body: "1rem"
  caption: "0.875rem"
```

- Display Font: Inter (headings, stats, CTAs)
- Body Font: Inter (body text, descriptions)
- Font sizes scale from 3rem (H1) down to 0.875rem (captions)

## 4. Components

Buttons use var(--color-primary) background with white text, 4px border radius, and 0.75rem 1.5rem padding. Cards have a 1px border in var(--color-neutral) at 20% opacity, 8px border radius, and 1.5rem padding. Badges use var(--color-accent) background.

## 5. Layout System

```yaml
grid_unit: 8px
max_width: 1280px
columns: 12
gutter: 24px
```

Base grid unit is 8px. Maximum content width 1280px. 12-column grid with 24px gutters. Slide padding is 3rem on all sides.

## 6. Depth & Shadows

```yaml
shadow_sm: "0 1px 2px rgba(0,0,0,0.05)"
shadow_md: "0 4px 6px rgba(0,0,0,0.07)"
shadow_lg: "0 10px 15px rgba(0,0,0,0.10)"
```

Minimal shadow usage. sm for cards, md for modals, lg for overlays.

## 7. Do's & Don'ts

DO: Use var(--color-primary) consistently for interactive and emphasis elements.
DO: Maintain a minimum contrast ratio of 4.5:1 for all text (WCAG AA).
DON'T: Mix more than two typefaces.
DON'T: Use decorative fonts for body text or data labels.
DON'T: Apply shadow-lg to more than one element per slide.

## 8. Responsive Behavior

```yaml
breakpoints:
  mobile: 640px
  tablet: 1024px
  desktop: 1280px
```

H1 scales from 3rem (desktop) to 2rem (tablet) to 1.5rem (mobile). Layout stack switches to single column below 640px. Font sizes use clamp() for fluid scaling between breakpoints.

## 9. Animation & Transitions

```yaml
duration_default: "200ms"
easing_default: "ease-in-out"
reveal_transition: "fade"
```

Default transition duration 200ms with ease-in-out. Reveal.js transition: fade. Avoid motion for users with prefers-reduced-motion.

## 10. Accessibility

```yaml
contrast_ratio_min: 4.5
wcag_level: "AA"
focus_ring: "2px solid #1a56db"
```

All text/background combinations meet WCAG 2.1 AA (4.5:1 minimum). Focus rings use var(--color-primary) at 2px solid. All images require alt text. Skip navigation link provided.

## 11. Agent Prompt Snippet

This is the Fixture Theme, a minimal design system for automated testing and validation purposes. It uses a clean blue-and-white palette built around Inter as the sole typeface. The primary color #1a56db conveys trust and professionalism, while the accent #e74694 draws attention to key metrics and calls to action. Use large, centered headings for title slides. Stat slides should feature the number prominently at 5rem or larger with the accent color, and the label in neutral below. Avoid decorative flourishes. Prefer whitespace over dense content. Maintain WCAG AA contrast at all times.
