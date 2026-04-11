# Theme CLI & Data Model Requirements Quality Checklist — 002-core-layouts-theme-system

**Purpose**: Unit-test the Theme CLI (FR-230–FR-239) and data model entity requirements for completeness, clarity, and traceability — not to verify implementation behavior.
**Created**: 2026-04-11
**Audience**: Author self-review before PR
**Domains**: Theme CLI subcommands, JSON output schemas, fuzzy search, create/use transactions, data model traceability

---

## Search vs --search Distinction

- [ ] CHK053 — Are `aio theme search` (a dedicated subcommand, FR-236) and `aio theme list --search` (an option on the list subcommand, FR-231) defined with distinct behavioral contracts? Specifically: do they return results in the same format, apply the same fuzzy matching algorithm, and use the same ranking criteria? Or is one a strict subset of the other? [Clarity, Spec §FR-231 vs §FR-236]
- [ ] CHK054 — Is the interaction between `--filter` and `--search` on `aio theme list` specified — in particular, are filters applied before or after fuzzy matching, and what is the result when both flags reduce the candidate set to zero? [Completeness, Gap — Spec §FR-231]

---

## JSON Output Schemas

- [ ] CHK055 — Are the JSON output schemas (field names, types, required vs optional) for `theme list --json`, `theme info --json`, and `theme search --json` formally defined in the spec or contracts? FR-238 states output "is valid JSON" but does not specify the schema; different subcommands could emit incompatible structures. [Completeness, Gap — Spec §FR-238]
- [ ] CHK056 — Is the JSON schema for `theme info --json` consistent with the `ThemeRecord` data model fields (`id`, `name`, `description`, `version`, `author`, `source_url`, `categories`, `colors`, `typography`)? US4 scenario 4 lists only a subset of keys (`id`, `name`, `author`, `categories`, `colors`, `typography`) — is the omission of `description`, `version`, and `source_url` intentional? [Consistency, Spec US4 §scenario 4 vs data-model.md §ThemeRecord]

---

## CLI Error Handling

- [ ] CHK057 — Is the stderr error message format for "theme not found" uniformly specified across all 6 subcommands, or only for `aio theme use` (where US4 scenario 9 gives the exact string)? Inconsistent error messages reduce scripting reliability. [Consistency, Gap — Spec US4 §scenario 9 vs §FR-239]
- [ ] CHK058 — Is the exit code and error behavior for `aio theme create {name}` when the name conflicts with an existing theme ID specified? FR-235 describes the happy path only; the conflict case has no acceptance scenario or FR. [Completeness, Gap — Spec §FR-235]
- [ ] CHK059 — Does the spec define the behavior of `aio theme show {id} --section N` when N is out of range (e.g., 0, 12, or a non-integer string)? FR-234 and the acceptance scenario only address the valid case (`--section 2`). [Coverage, Edge Case, Spec §FR-234]

---

## Fuzzy Match Algorithm

- [ ] CHK060 — Is the fuzzy matching algorithm for `aio theme search` specified beyond "difflib or Levenshtein"? Without a specified similarity threshold (e.g., cutoff score, minimum character overlap), two conforming implementations can return incompatible result sets for the same query. [Clarity, Spec §FR-236]
- [ ] CHK061 — Is there a requirement defining the maximum number of results returned by `aio theme search` when no `--limit` is provided? FR-236 and the acceptance scenario (SC-233: "40+ themes") imply no cap, but returning all 64 themes for a single-character query may not match intended behavior. [Completeness, Gap — Spec §FR-236]

---

## Theme Create & Use Transaction Safety

- [ ] CHK062 — Is the transaction order for `aio theme create` defined: is the theme directory created on disk before or after `registry.json` is updated? Defining the order determines the recovery path if the operation fails midway (e.g., directory exists but registry is stale). [Clarity, Gap — Spec §FR-235]
- [ ] CHK063 — Does the spec define what `aio theme use {id}` does when there is no `.aio/config.yaml` — i.e., the command is run outside an initialized project directory? FR-233 assumes a project context but does not define the out-of-project failure mode. [Coverage, Edge Case, Spec §FR-233]

---

## Data Model Traceability

- [ ] CHK064 — Is the `DesignSection` minimum content requirement (`char_count ≥ 50` per section, `char_count ≥ 200` for section 11) traceable to a spec FR? These constraints appear only in `data-model.md` but have no FR anchor. If the FR is missing, the constraints are invisible to spec reviewers and may be dropped during implementation. [Completeness, Traceability Gap — data-model.md §DesignSection vs Spec §FR-220]
- [ ] CHK065 — Is the requirement that exactly one `LayoutTemplate` in the registry must have `is_fallback = True` traceable to a spec FR? FR-248 says "falls back to `content`" but does not name the singleton fallback mechanism; the enforcement rule lives only in `data-model.md`. [Traceability, Spec §FR-248 vs data-model.md §LayoutTemplate]
- [ ] CHK066 — Are the required minimum keys for `ThemeRecord.colors` (`primary`, `background`, `text`) specified in the FRs? FR-213 lists CSS custom property naming conventions but does not declare which semantic tokens are mandatory. The constraint appears only in `data-model.md`, leaving the spec incomplete as a standalone document. [Completeness, Traceability Gap — Spec §FR-213 vs data-model.md §ThemeRecord]
- [ ] CHK067 — Is the `HotReloadEvent.event_type = "error"` branch — where the SSE endpoint sends an error event to connected browsers when a rebuild fails — specified in the FRs? FR-252 and FR-257 describe only the `"reload"` event path; the error event contract appears only in `data-model.md`. [Completeness, Gap — Spec §FR-252 vs data-model.md §HotReloadEvent]
- [ ] CHK068 — Is there a spec requirement that `BuildResult.layout_histogram` values must sum exactly to `slide_count`? This invariant is stated in `data-model.md` but has no corresponding FR, meaning it is not part of the testable specification. [Traceability, data-model.md §BuildResult]
