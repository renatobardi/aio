# Modern Theme — DESIGN.md

## Visual Theme

Contemporary corporate aesthetic with bold typography and purposeful color use.
Inspiration: Material Design 3, Figma-era product design. Target audience: product
managers, startup teams, business professionals seeking a polished look.

## Color Palette

- Primary: `#0f172a` — headings, primary text
- Secondary: `#475569` — body text, captions
- Accent: `#6366f1` — interactive elements, highlights
- Background: `#ffffff` — slide background
- Surface: `#f8fafc` — cards, sidebars
- Danger: `#ef4444` — errors, alerts
- Contrast ratios: Primary on Background = 18.1:1 (AAA)

## Typography

- Heading font: "Plus Jakarta Sans", system-ui, sans-serif
- Body font: "DM Sans", system-ui, sans-serif
- Code font: "Fira Code", monospace
- H1: 3.5rem / 1.05 line-height / 800 weight
- H2: 2.25rem / 1.15 line-height / 700 weight
- Body: 1.125rem / 1.65 line-height / 400 weight

## Components

**Buttons**: Rounded-full, gradient accent. Primary: `#6366f1`→`#8b5cf6`.
**Badges**: Pill shape, colored by semantic meaning.
**Cards**: White bg, subtle shadow, `0.75rem` radius.
**Callouts**: Solid left border, tinted background matching accent.
**Code blocks**: Dark theme (`#0f172a` bg), Fira Code, syntax highlighted.

## Layout System

- Grid: 12-column, `2rem` gutter
- Spacing scale: 0.25 / 0.5 / 1 / 2 / 3 / 4 / 6 / 8rem
- Slide safe area: 4rem horizontal, 3rem vertical
- Max content width: 60rem

## Depth & Shadows

- Level 0 (flat): no shadow
- Level 1 (card): `0 1px 4px rgba(15,23,42,0.06), 0 2px 8px rgba(15,23,42,0.04)`
- Level 2 (modal): `0 8px 24px rgba(15,23,42,0.10)`
- Level 3 (overlay): `0 16px 48px rgba(15,23,42,0.14)`
- Level 4 (toast): `0 24px 64px rgba(15,23,42,0.18)`

## Do's & Don'ts

**Do:**
- Use bold weight for key statistics and callouts
- Pair accent color with white text for CTAs
- Use the two-column layout for comparisons

**Don't:**
- Use more than 3 colors per slide
- Mix heading font weights inconsistently
- Use low-contrast text on accent backgrounds

## Responsive Behavior

- Mobile: Single column, H1 scales to 2.5rem, spacing halved
- Tablet: Reduced multi-column support
- Desktop: Full grid with generous whitespace

## Animation & Transitions

- Slide entrance: slide-up 250ms ease-out
- List items: fade-in with 50ms stagger
- `prefers-reduced-motion`: all animations disabled
- Easing: `cubic-bezier(0.25, 0.46, 0.45, 0.94)`

## Accessibility

- WCAG 2.1 AA for all text/background combinations
- Focus ring: `3px #6366f1` offset
- All icons have `aria-hidden="true"` or descriptive `aria-label`
- Color not used as sole indicator

## Agent Prompt Snippet

The **Modern** theme uses deep navy (`#0f172a`) on white, with indigo accent (`#6366f1`).
Typography is "Plus Jakarta Sans" at 3.5rem H1 / 2.25rem H2 / 1.125rem body — bold and
punchy. Layout has generous 4rem horizontal padding and 8-step spacing scale.

Generate slides that lead with big numbers or bold claims; support with brief text.
Use `hero-title` for openers, `stat-highlight` or `two-column` for comparisons.
The indigo accent should appear on exactly one focal element per slide.
