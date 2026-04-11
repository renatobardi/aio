# Build Pipeline & Serve Requirements Quality Checklist — 002-core-layouts-theme-system

**Purpose**: Unit-test the build pipeline (FR-240–FR-249) and serve/hot-reload (FR-250–FR-257) requirements for completeness, clarity, and consistency — not to verify implementation behavior.
**Created**: 2026-04-11
**Audience**: Author self-review before PR
**Domains**: Build pipeline steps, dry-run, layout inference, logging, SSE serve, watchdog, SIGINT shutdown

---

## Step Handoff Contracts

- [ ] CHK036 — Is the output type of each pipeline step formally specified as the input type of the next step? (e.g., what does PARSE return that ANALYZE consumes? What does ANALYZE return that COMPOSE consumes?) Without typed step contracts, the boundary between steps is implementation-defined rather than specification-defined. [Completeness, Gap — Spec §FR-240–§FR-245]
- [ ] CHK037 — Is the ANALYZE step's per-slide output (resolved layout_id + extracted context fields) specified as a named type, or only implied through `SlideRenderContext`? If ANALYZE produces an intermediate representation before COMPOSE constructs `SlideRenderContext`, that intermediate type is unspecified. [Clarity, Gap — Spec §FR-242 vs data-model.md §SlideRenderContext]

---

## Error Propagation

- [ ] CHK038 — Does the spec define whether a COMPOSE failure on slide N halts the entire pipeline or skips the failing slide and continues? FR-243 and FR-248 describe the happy path and the unknown-layout fallback, but a hard composition error (e.g., missing required context field) has no specified behavior. [Completeness, Gap — Spec §FR-243]
- [ ] CHK039 — Is the exit code for `InlineError` (triggered when an external URL is detected during the INLINE step, per FR-245) specified? Build scenario 7 specifies exit code 2 for a missing theme file, but no acceptance scenario or FR captures the exit code for the external-URL failure path. [Clarity, Gap — Spec §FR-245]
- [ ] CHK040 — Are the stderr message format requirements (step name, failing component, file reference) consistently defined for all five pipeline failure modes (parse error, unknown theme, composition error, render error, inline/external-URL error)? Or are formats only implied by individual acceptance scenarios? [Consistency, Gap — Spec §FR-247]

---

## Dry-Run Completeness

- [ ] CHK041 — Does FR-249 specify whether `--dry-run` executes all 5 pipeline steps (including INLINE) and only skips the file write, or whether it halts before INLINE? The acceptance scenario says "all 5 steps are executed and logged" but the FR says "skips file write; logs planned byte count" — are both consistent? [Clarity, Spec §FR-249 vs US5 §scenario 5]
- [ ] CHK042 — Is the "planned byte count" in `--dry-run` defined as the pre-inline size (composed HTML before asset embedding), the estimated post-inline size, or the actual in-memory post-inline size? Each produces a significantly different number for a typical 30-slide deck. [Clarity, Spec §FR-249]

---

## Layout Inference

- [ ] CHK043 — Are all four inference patterns in FR-246 (stat, quote, list, image) defined with measurable trigger criteria — e.g., specific regex patterns, content size thresholds, or keyword presence rules — or are they described only by example? Without criteria, two implementations may infer different layouts for the same content. [Clarity, Spec §FR-246]
- [ ] CHK044 — Does the spec define the behavior when the ANALYZE step's inferred layout conflicts with an explicit `@layout:` directive in the slide? Is the explicit directive always authoritative, or does ANALYZE override it? [Completeness, Gap — Spec §FR-242]

---

## Log Contract

- [ ] CHK045 — Is the exact step-boundary log format (e.g., `[INFO] Step N/5: NAME`) specified in the FRs or only illustrated in the acceptance scenario? If the format is not normative, tests cannot assert on log output reliably. [Clarity, Spec §FR-247 vs US5 §scenario 1]
- [ ] CHK046 — Is there a requirement specifying the content of per-slide DEBUG log entries — specifically which fields (slide index, layout_id, resolved context keys, byte count) must appear — or is "DEBUG per-slide" the only constraint? [Completeness, Spec §FR-247]

---

## Serve / SSE Endpoint

- [ ] CHK047 — Is the initial SSE handshake event format defined in the FRs? Acceptance scenario US6.1 mentions `{"type":"connected"}` as the first event sent after a client connects, but no FR captures this requirement. If the contract is only in the scenario, it may be missed during implementation. [Completeness, Gap — Spec US6 §scenario 1 vs §FR-252]
- [ ] CHK048 — Does the spec specify whether the watchdog in FR-253 uses inotify/kqueue event-driven detection or polling-based detection? Event-driven and polling modes have different latency characteristics and OS portability constraints that affect whether SC-251 (< 2s reload) is achievable. [Clarity, Spec §FR-253]
- [ ] CHK049 — Does FR-256 define the shutdown order for SIGINT — specifically, is the SSE socket closed before or after the watchdog observer is stopped? An undefined order can cause the watchdog to fire a rebuild event after the SSE channel is closed, producing a spurious error log. [Clarity, Spec §FR-256]
- [ ] CHK050 — Is there a requirement specifying the maximum buffer size of the `asyncio.Queue` used for hot-reload events between the watchdog thread and the SSE handler coroutine? Without a bound, a slow SSE consumer can cause unbounded memory growth during rapid file-save sequences. [Completeness, Gap]

---

## Inline Step

- [ ] CHK051 — Are the image inlining requirement in FR-204 (base64 inline for split-image-text, max 3 MB) and the asset embedding requirement in FR-245 (INLINE step embeds "all assets") specified as the same operation or two distinct passes? If they are the same INLINE step, does the 3 MB limit apply globally to all inlined images or only to split-image-text? [Consistency, Spec §FR-204 vs §FR-245]
- [ ] CHK052 — Is there a requirement specifying that literal `</script>` substrings inside inlined vendor JavaScript must be escaped (e.g., to `<\/script>`) to prevent premature HTML `<script>` tag closure? This is referenced in the CLAUDE.md constitution but does not appear as an explicit FR. [Completeness, Gap — Constitution Rule 5 vs Spec §FR-244]
