# Performance Requirements Quality Checklist — 002-core-layouts-theme-system

**Purpose**: Unit-test the performance requirements in `spec.md` for measurability, completeness, and consistency — not to verify that timing targets are met.
**Created**: 2026-04-11
**Audience**: Author self-review before PR
**Domains**: Build pipeline, theme CLI, hot-reload serve, import script, layout engine

---

## Requirement Measurability

- [ ] CHK020 — Is SC-200 ("each layout renders in under 10ms") defined with clear measurement conditions? Specifically: warm Jinja2 environment or cold? With or without theme CSS vars? In isolation (no I/O) or as part of the pipeline? [Measurability, Spec §SC-200]
- [ ] CHK021 — Is SC-205 ("build with all 8 layouts < 30s for 30 slides") and SC-240 ("full build of 30 slides < 30s") the same requirement? If so, is the duplication intentional, or are the two criteria measuring different things (P1 vs P5 scope)? [Consistency, Spec §SC-205 vs §SC-240]
- [ ] CHK022 — Do the performance targets (SC-200, SC-205, SC-240, SC-250, SC-251) specify the hardware baseline? ("i5, 8GB RAM" is mentioned in the constitution but not in the spec FRs — is this traceability gap intentional?) [Clarity, Spec §SC-205, Constitution Performance section]
- [ ] CHK023 — Is SC-212 ("import script < 2 minutes") defined with network conditions? (Residential broadband? Corporate proxy? Offline/throttled CI?) A 2-minute target on a slow connection versus a fast one produces different acceptance boundaries. [Clarity, Spec §SC-212]
- [ ] CHK024 — Is SC-250 ("server starts in under 2 seconds") measuring wall-clock time from command invocation, or time-to-first-byte at `GET /`? These differ by up to 1s depending on initial build time. [Clarity, Spec §SC-250]
- [ ] CHK025 — Is SC-251/FR-254 ("reload event within 2 seconds of file change") measuring from file-save timestamp, from watchdog detection, or from SSE delivery? Each has different latency characteristics. [Clarity, Spec §SC-251, §FR-254]

---

## Requirement Completeness

- [ ] CHK026 — Are performance requirements defined for `aio theme create` and `aio theme show`? Both commands perform file I/O and DESIGN.md parsing, but no timing targets appear in the Success Criteria section. [Completeness, Gap — Spec §SC-230 covers list/info/use/search but not create/show]
- [ ] CHK027 — Is there a performance requirement for parsing the DESIGN.md of a single theme? SC-220 covers correctness but no timing target exists for the parser (relevant for `aio theme info` latency). [Completeness, Gap]
- [ ] CHK028 — Is there a memory usage requirement? The constitution mentions "< 150 MB install size" but no runtime memory ceiling is defined for the build pipeline or the serve process. [Completeness, Gap]
- [ ] CHK029 — Is there a performance requirement for the JSON output path (`--json` flag on `theme list`, `theme info`, `theme search`)? Serialisation of 64+ theme records may differ significantly from Rich table rendering. [Completeness, Gap]

---

## Scenario Coverage

- [ ] CHK030 — Are performance requirements defined for slide counts beyond 30? What is the expected degradation model — linear, O(n log n), or O(n²)? Without this, the "< 30s for 30 slides" target cannot be extrapolated to real-world use cases. [Coverage, Edge Case, Spec §SC-205]
- [ ] CHK031 — Are performance requirements defined for concurrent SSE clients in `aio serve`? (1 browser tab vs. 5 tabs — is the reload broadcast O(1) or O(n) in time?) [Coverage, Edge Case, Spec §FR-254]
- [ ] CHK032 — Is there a performance requirement for the `aio theme list` command with no themes installed? An empty registry is an edge case that may bypass caching paths. [Coverage, Edge Case, Spec §SC-210]
- [ ] CHK033 — Are performance requirements defined for the `--enrich` image generation path? Image download + base64 conversion is the dominant latency in an enriched build, yet no target is specified. [Coverage, Gap — FR-249 flags --enrich as opt-in but no SC covers its timing]

---

## Consistency

- [ ] CHK034 — Are SC-210 ("theme list < 1s") and SC-230 ("theme list < 1s") the same requirement restated under two user stories (P2 and P4)? If intentional, is the rationale documented? [Consistency, Spec §SC-210 vs §SC-230]
- [ ] CHK035 — Does the "< 2 seconds" hot-reload target (SC-251) include the rebuild time? FR-254 says "rebuild on change < 2s for ≤ 30 slides" and SC-251 says "reload event within 2 seconds". If the rebuild itself takes up to 2s, there is no budget left for watchdog detection + SSE delivery. Are these targets consistent? [Consistency, Spec §SC-251 vs §FR-254]
