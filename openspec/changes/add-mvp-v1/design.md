# Design

## Context

See proposal.md for motivation. Current implementation state as of 2026-09-22:

- `data_acquisition/eba_exercises.py` is real and working (verified against live EBA
  pages): bulk CSV download plus `build_entities_csv()` for Transparency
  Exercise/Stress Test years.
- `data_acquisition/edap_downloader.fetch_module()` — the interface `run_update.py`
  and the rest of the pipeline call for P3DH — is currently a stub that
  unconditionally raises `BulkAccessNotConfirmed`. AGENTS.md's repo-layout summary
  describes it as "currently delegates to `edap_scraper`"; that is the intended
  end state, not the current one — the two are not yet wired together. Wiring them
  is task 1.1.
- `data_acquisition/edap_scraper.py` is an unverified skeleton against P3DH's
  Power BI-embedded "Data Points Report" (see its own docstring for exactly what's
  confirmed vs. guessed).
- `data/entities.csv` and `data/modules.txt` do not exist yet (only
  `entities.csv.example`) — `run_update.py` and `entities.load_entities()` both
  refuse to run without them.
- No package-surface or reconciliation code exists yet; this change defines both.
- No pilot banks have been chosen yet.

## Goals / Non-Goals

**Goals:**
- Define how source-specific reporting items map to standardized concepts.
- Define how provenance (reported actual vs. scenario-projected) is attached to a
  figure, and how that stays cheap and reliable rather than inferred.
- Define the returned DataFrame's schema.
- Define how "missing from source" and "retrieval/processing failed" stay distinct
  end to end, including the specific gap found in `run_update.py`'s current
  failure handling.

**Non-Goals:**
- Normalizing figures across accounting standards, consolidation scopes, or
  reporting frameworks (proposal.md / README section 3 — out of scope by design,
  not deferred).
- Implementing the ESEF acquisition path itself (not started; `filings.xbrl.org`
  is the planned starting point per AGENTS.md, but that's its own acquisition
  module, not a reconciliation-layer design decision).
- Choosing the actual pilot banks (left as an open question below).

## Decisions

### 1. Static per-item lookup table for concept mapping, not pattern/anchor matching

A source-specific reporting item maps to a standardized concept via an explicit
table keyed on `(source, reporting_item_code) -> standardized_concept`, maintained
by hand as pilot banks and variables are added — not inferred by matching on
labels, XBRL anchors, or similar heuristics.

**Alternatives considered:**
- *Pattern/XBRL-anchor matching*: scales without per-item curation, but risks two
  failure modes that are worse than curation cost here: false equivalence (a
  narrower- or differently-scoped anchor treated as the same concept) and false
  negatives (a bank-specific label missed and wrongly reported as
  missing-from-source). Either failure is silent unless specifically tested for.
- *Hybrid (anchor-matching suggests candidates, a human confirms)*: reduces
  curation effort at larger scale, but adds a review workflow this project has no
  need for yet, given v1's scope.

**Why the static table wins for v1:** README section 3 already commits to "a
defined set" of banks and variables, not comprehensive coverage — so the table's
curation cost is bounded, not open-ended. A static table is also directly
reviewable (a diff shows exactly what changed) and fails safe: an item with no
entry is reported as unmapped rather than silently mapped wrong. Revisit the
hybrid approach only if a future change expands scope past what hand-curation
supports.

### 2. Provenance is a small closed mapping set at ingestion, not inferred from the data

Provenance (`reported_actual` / `scenario_projection` / `restated_actual`) is
determined entirely by which acquisition module produced a figure, which
arguments it was called with, and — for `eba_exercises.py`'s stress-test
exercise specifically — the row's own `Scenario` code, never by inspecting the
figure's value or label. Concretely:

| Source module | Call | Scenario code | Provenance |
|---|---|---|---|
| `eba_exercises.py` | `exercise="transparency"` | n/a | `reported_actual` |
| `eba_exercises.py` | `exercise="stress_test"` | 1 (Actual figures) | `reported_actual` |
| `eba_exercises.py` | `exercise="stress_test"` | 2 (Baseline) / 3 (Adverse) | `scenario_projection` |
| `eba_exercises.py` | `exercise="stress_test"` | 11 (Restated) | `restated_actual` |
| `edap_downloader.py` (P3DH) | any | n/a | `reported_actual` |
| `esef_client.py` (ESEF, via filings.xbrl.org) | any | n/a | `reported_actual` |

**Revised during implementation (2026-09-25):** the original version of this
table treated `exercise="stress_test"` as uniformly `scenario_projection`.
Running `eba_exercises.py` for real against the 2025 Stress Test bulk CSV
(`data/raw/stress_test/2025/TRA_OTH.csv`) showed its own `Scenario` column
(confirmed against that download's `Metadata_TR.xlsx`, sheet "Scenario") mixes
a reported-actual starting point (code 1) and a later restatement of it (code
11) alongside the baseline/adverse projections (codes 2/3) in the same file —
so provenance for this source is scenario-code-scoped, not exercise-scoped.
This is still a fixed table, not inferential logic: the code reads a value
EBA itself attaches to the row, never the figure's magnitude or label, so
Requirement 3's falsifiability contract stays cheap. See
`data_acquisition/reconcile.py`'s `_SCENARIO_PROVENANCE` table.

### 3. Returned DataFrame schema

One row per `(bank, period, standardized_concept, source)` combination:

`bank_lei, period, standardized_concept, source_reporting_item, source, provenance, value, status, origin_reference`

- `status`: `ok` / `missing_from_source` / `retrieval_failed` (see decision 4).
- `origin_reference`: enough to identify the exact publication/exercise/report the
  figure came from (spec's "Figure traceable to its origin" scenario) — e.g. exercise
  name + year for Transparency/Stress Test, or wave id + module for P3DH.
- When more than one wired-up source reports the same concept for a bank/period,
  this produces multiple rows (one per source), each with its own `provenance` and
  `origin_reference` — never a single combined row (spec's "Multiple sources"
  scenario).

### 4. Missing-from-source, not-yet-published, and retrieval-failed are three distinct outcomes

Found during this session: `run_update.py`'s current per-item loop has only one
`except Exception` branch, which records both "this wave hasn't published yet"
(an EBA-confirmed normal outcome, not a failure — see AGENTS.md's P3DH bullet)
and a genuine scraper/network failure as the same `status: "failed"`. That
conflation is task 1.4.

Design direction: `edap_downloader.fetch_module()` should be able to raise a
distinct `NotYetPublished` exception (a sibling of, not a subclass conflated
with, a generic fetch failure), which `run_update.py` catches separately and
records as `status: "not_yet_published"`. At the package-surface level, this is
orthogonal to `missing_from_source` (the source doesn't report the concept at
all, ever) — a wave not yet published is a *timing* state on data acquisition,
not a value the reconciliation layer would return as a DataFrame row at all.

## Risks / Trade-offs

- **Power BI's DOM is not a stable public contract; slicer selectors in
  `edap_scraper.py` are unverified** → Mitigation: `edap_scraper` already raises a
  field-specific `TimeoutError` naming exactly which slicer broke, so failures are
  diagnosable rather than opaque; task 1.1 does the actual verification.
- **`entities.csv` seeded from the Transparency Exercise participant list is a
  proxy for "who's live on P3DH," not confirmed ground truth** (EBA confirmed no
  separate institution list exists) → Mitigation: cross-check against the
  scraper's own discovered Entity slicer values once 1.1 is verified, and log
  mismatches rather than silently trusting either list (task 1.2).
- **`waves.py` doesn't generate year-end waves for non-December reference
  dates**, though EBA's FAQ B2 confirms they're expected too → Mitigation: confirm
  first whether any pilot bank actually has a non-December fiscal year-end before
  generalizing `_reference_dates_since()` speculatively (task 1.5).
- **The static concept-mapping table has a linear curation cost per bank/variable
  added** → Accepted trade-off for v1's intentionally bounded scope; revisit only
  if a later change expands coverage past what hand-curation supports.
- **No EU-wide bulk source exists for ESEF filings; `filings.xbrl.org` has known
  coverage gaps (e.g. Germany, Ireland)** → Mitigation: favor pilot banks from
  countries `filings.xbrl.org` covers well, or document a per-bank IR-page
  fallback in `entities.csv`'s `notes` column.

## Open Questions

- Does P3DH's Entity slicer take an LEI or a display name, and are "Module" and
  "Template" the same list or two separate ones? Task 1.1 answers this
  empirically; it changes `edap_scraper`'s selector/value handling, not the
  concept-mapping, provenance, schema, or task breakdown above.
- Which specific banks make up v1's pilot set? Affects task 1.2/1.5's fiscal
  year-end check and which countries matter for ESEF coverage, but doesn't change
  any decision recorded above regardless of which banks are chosen.
