# Vibrant Theme — DESIGN.md

## 1. Visual Theme

High-energy aesthetic with rich colors for creative and marketing presentations.
Inspiration: Dribbble gradients, Stripe branding, modern SaaS landing pages.
Target audience: designers, marketers, founders pitching to investors.

## 2. Color Palette

- Primary: `#1e1b4b` — headings
- Secondary: `#4c1d95` — subheadings
- Accent: `#f59e0b` — CTAs, highlights
- Background: `#0f0a1e` — dark slide background
- Surface: `#1e1b4b` — cards on dark bg
- Danger: `#f43f5e` — errors
- Gradient: `#7c3aed` → `#2563eb` — hero backgrounds
- Contrast: Accent on Background = 10.2:1 (AAA)

## 3. Typography

- Heading font: "Cabinet Grotesk", system-ui, sans-serif
- Body font: "Satoshi", system-ui, sans-serif
- Code font: "Berkeley Mono", monospace
- H1: 4rem / 1.0 line-height / 900 weight
- H2: 2.5rem / 1.1 line-height / 700 weight
- Body: 1.25rem / 1.55 line-height / 400 weight

## 4. Components

**Buttons**: Gradient bg, pill shape, bold weight, glow shadow.
**Badges**: Neon-style with colored glow on dark background.
**Cards**: Dark surface with gradient border, `1rem` radius.
**Callouts**: Gradient left border, semi-transparent dark background.
**Code blocks**: Dark bg with neon syntax highlighting.

## 5. Layout System

- Grid: 12-column, `2rem` gutter, dark background
- Spacing scale: 0.5 / 1 / 1.5 / 2 / 3 / 4 / 6 / 8rem
- Slide safe area: 4rem horizontal, 3.5rem vertical
- Max content width: 64rem

## 6. Depth & Shadows

- Level 0: no shadow
- Level 1: `0 2px 8px rgba(124,58,237,0.15)`
- Level 2: `0 8px 32px rgba(124,58,237,0.25)`
- Level 3: `0 16px 48px rgba(124,58,237,0.35)`
- Level 4: `0 0 64px rgba(124,58,237,0.50)` (glow effect)

## 7. Do's & Don'ts

**Do:**
- Use gradient backgrounds for hero slides
- Pair yellow accent with dark backgrounds for maximum contrast
- Use the gallery and full-image layouts liberally

**Don't:**
- Use dark text on dark backgrounds (accessibility failure)
- Overload slides with more than 3 accent colors
- Use thin font weights on dark backgrounds

## 8. Responsive Behavior

- Mobile: Gradients simplified to solid colors, font scales 25% smaller
- Tablet: Reduced grid columns, maintained dark aesthetic
- Desktop: Full gradient + animation experience

## 9. Animation & Transitions

- Slide transition: zoom-fade 400ms cubic-bezier(0.34, 1.56, 0.64, 1)
- Hero elements: scale-up entrance 300ms spring
- `prefers-reduced-motion`: fade only, 200ms
- Particles/glow: CSS-only, no JS animation libraries

## 10. Accessibility

- WCAG 2.1 AA on dark background for all text colors
- High-contrast mode: toggle forces `#ffffff` text on `#000000` bg
- Focus ring: `3px #f59e0b` — visible on both light and dark
- Never rely on color alone for meaning

## 11. Agent Prompt Snippet

The **Vibrant** theme uses a dark background (`#0f0a1e`) with purple-to-blue gradients
and yellow accent (`#f59e0b`). Typography is ultra-bold Cabinet Grotesk at 4rem H1.

Generate slides that are visual-forward: lead with big imagery or bold stats, use
short (< 8 word) headings, and place text over gradient overlays. Use `hero-title`
with gradient classes, `gallery` for multiple images, `quote` for testimonials.
Yellow accent appears on the single most important word or stat per slide.
