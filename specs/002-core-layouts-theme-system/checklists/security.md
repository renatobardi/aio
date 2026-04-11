# Security Requirements Quality Checklist — 002-core-layouts-theme-system

**Purpose**: Unit-test the security requirements in `spec.md` for completeness, clarity, and coverage — not to verify implementation behavior.
**Created**: 2026-04-11
**Audience**: Author self-review before PR
**Domains**: Input sanitization, output safety, dependency security, injection prevention

---

## Requirement Completeness

- [ ] CHK001 — Is a requirement explicitly stating that `yaml.safe_load()` must be used for all YAML parsing (frontmatter, DESIGN.md fenced blocks, config.yaml) present in the spec FRs, not just in CLAUDE.md? [Completeness, Gap — constitution rule enforced at code level only]
- [ ] CHK002 — Does the SVG sanitization requirement (Constitution Art. III / tasks T024) specify *which* SVG elements and attributes are stripped beyond `<script>`? (e.g., `onload`, `onerror`, `<use href>`, `javascript:` hrefs are equally dangerous) [Completeness, Spec §FR-208 adjacent, Gap]
- [ ] CHK003 — Is there a requirement defining what happens when an inlined `theme.css` or `layout.css` contains `url()` with an `https://` reference (e.g., a malicious or misconfigured theme with an external font URL)? [Completeness, Gap — external-URL check in FR-245 applies to HTML output, but theme CSS is inlined before the check]
- [ ] CHK004 — Is the scope of the `ExternalURLError` check (FR-245) explicitly stated as applying *after* CSS inlining, so that `url()` values inside `<style>` blocks are also scanned? [Clarity, Spec §FR-245]
- [ ] CHK005 — Is there a requirement preventing Markdown injection through the layout context variables? Specifically, is it specified that `title` and `body_html` are HTML-escaped or sanitized before Jinja2 receives them, beyond the "pre-rendered by mistune" note in FR-207? [Completeness, Spec §FR-207]
- [ ] CHK006 — Is there a requirement about sanitizing the Agent Prompt Snippet (DESIGN.md section 11) before it is embedded in the output HTML? A malicious theme could contain `<script>` inside section 11. [Completeness, Gap — Spec §FR-257 adjacent]

---

## Requirement Clarity

- [ ] CHK007 — Is "SVG sanitization" in the spec defined with a measurable, testable boundary? ("No `<script>` tags" is mentioned in tasks T024, but is the full set of disallowed constructs unambiguous in the spec FRs?) [Clarity, Ambiguity]
- [ ] CHK008 — Is the `@font-face src:` URL stripping requirement specified with enough clarity to determine what counts as an "external URL" in CSS context (e.g., does `url('data:...')` pass? does `url('/fonts/x.woff2')` pass?) [Clarity, Spec §FR-245]
- [ ] CHK009 — Is "HTML output escaped (prevent XSS if slides have user input)" from the constitution translated into a concrete FR? The spec describes slides as authored content, but the boundary between trusted author content and untrusted input is unspecified. [Clarity, Gap — Constitution Security constraint vs no FR]
- [ ] CHK010 — Does FR-216 (import script using `subprocess.run(["git", ...])`) specify that the repository URL is hardcoded (not user-supplied) to prevent argument injection? [Clarity, Spec §FR-216]

---

## Scenario Coverage

- [ ] CHK011 — Are requirements defined for the case where a DESIGN.md from awesome-design-md contains a fenced YAML block with YAML anchors or aliases that could cause anchor bomb / billion-laughs denial-of-service? (`yaml.safe_load()` mitigates this, but is the requirement to use it grounded in spec FRs?) [Coverage, Edge Case]
- [ ] CHK012 — Is there a requirement for input size bounds on YAML frontmatter, DESIGN.md content, and `slides.md`? Without a maximum input size, a crafted large file could cause a DoS via memory exhaustion. [Coverage, Gap]
- [ ] CHK013 — Is there a requirement specifying that the `SECTION_RE` regex in `parse_design_md()` is validated against catastrophic backtracking (ReDoS)? The `.*?` non-greedy patterns with `re.DOTALL` on large inputs are a known risk. [Coverage, Edge Case, Spec §FR-221 / tasks T027]
- [ ] CHK014 — Is there a requirement addressing what happens when a theme's `theme.css` or `layout.css` contains CSS that breaks out of the `<style>` block (e.g., `</style>` inside a CSS string)? [Coverage, Edge Case]
- [ ] CHK015 — Is the security boundary for `--enrich` (Pollinations.ai image fetch) defined? Specifically, is there a requirement that the image URL passed to Pollinations.ai is sanitized and not user-controlled in a way that enables SSRF? [Coverage, Gap — Spec §FR-249 mentions --enrich flag but no security constraint]

---

## Consistency

- [ ] CHK016 — Is the external-URL prohibition (Art. II / FR-245) consistently applied in requirements for all asset types: CSS `url()`, `@font-face src:`, SVG `<image href>`, and HTML `src=`/`href=`? Or does the spec only address HTML-attribute-level URLs? [Consistency, Spec §FR-245 vs Constitution Art. II]
- [ ] CHK017 — Do the security requirements in spec.md align with the constitution's security constraints (yaml.safe_load, SVG sanitization, HTML escaping, no RCE via YAML)? Are all four constitution security rules traceable to at least one FR? [Consistency, Traceability]

---

## Non-Functional Requirements Quality

- [ ] CHK018 — Is the threat model for this feature documented anywhere, even as a brief enumeration of attack surfaces? (template injection, YAML RCE, XSS via SVG, SSRF via image fetch, CSS injection, import script) [Completeness, Gap]
- [ ] CHK019 — Are there measurable acceptance criteria for the SVG sanitization requirement? (e.g., "no `<script>`, `onload`, `onerror`, or `javascript:` attributes survive the sanitizer") or is the current spec only testable by implementation inspection? [Measurability, Spec §Constitution Art. III]
