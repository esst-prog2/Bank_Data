# Proposal

## Why

Code review feedback on Homework 7/8 (2026-11-08) flagged two real problems with the
demo as it stood:

1. The dashboard HTML the demo is actually run from, and the script that precomputes
   its numbers, were never committed - only their output (two static package-call
   snapshots, `docs/review.html`/`compare.html`) lived in the repository. The program
   the audience scores at the final has to be the one in the repository, not a file
   that only ever existed on one machine's Desktop.
2. Homework 7 asked whether a real, unresolved disagreement between two independently
   reported RWA totals for the same bank/period (Erste Group's EU KM1 vs EU OV1
   templates, ~1.5% apart) should be shown live in the demo, or whether an unexplained
   discrepancy reads as "not finished." The review's answer: show it. Returning both
   figures, each tagged by its source template, is the entire point of this project's
   provenance design (`get_financial_data()` never silently reconciles multiple
   sources into one value) - collapsing it to one number in the results table for
   presentation purposes contradicted that design instead of demonstrating it.

A side effect of actually committing the dashboard generator for review was finding a
real portability bug worth fixing in the same pass: the shipped HTML referenced its
bank logos and country flags via absolute `file:///` paths into one machine's Desktop
folder. Even once committed, that file would render with every image broken on any
other machine - the opposite of the "fresh clone" trustworthiness this project has
otherwise tried to earn (see Homework 7's test-suite fragility fix).

## What Changes

- Added `dashboard/` to the repository: the precompute script
  (`build_comparison_data.py`, calling `get_financial_data()` /
  `compute_rwa_density()` / `compute_cost_to_income_ratio()` /
  `compute_npl_ratio()` exactly as shipped, unchanged from before), the HTML
  assembly script (`build_dashboard.py`), and every input they need to run from a
  fresh clone (`pilot_28_leis.json`, `total_assets.json`, `europe_map.svg`,
  `bank_logos/`, `country_flags/`) - nothing left on a machine the repository can't
  see.
- `build_dashboard.py` now inlines every logo and flag as a base64 data URI instead
  of an absolute `file:///` path, so the generated HTML has zero external file
  dependencies - open it anywhere, no sibling folders required.
- `build_comparison_data.py`'s `pick_best_row()` now detects a genuine disagreement
  among same-tier `reported_actual` rows (not scenario-projection rows, which
  legitimately differ by stress-test scenario rather than disagreeing about a
  reported fact) and, when one exists, keeps every disagreeing figure - tagged by
  its own source template - on the cell instead of silently resolving to one number.
  Found by the same check across all 28 pilot banks: 2 of 28 have a real
  `total_risk_exposure_amount` disagreement this way (Erste Group, ~1.5%; one other
  pilot bank, ~0.3%), confirming this isn't a one-off.
- The results table renders a disagreement cell distinctly (amber background/border)
  showing every value, with a hover tooltip giving the exact figures, their source
  templates, and the percentage gap - one sentence turning an apparent inconsistency
  into visible evidence that the provenance design works, per the review's answer.
  Disagreement cells are excluded from "best value" highlighting (there's no single
  number to rank when the sources themselves disagree).
- The generated dashboard is published at `docs/dashboard.html` (served via GitHub
  Pages, same convention as the existing `docs/review.html`/`compare.html`
  snapshots), and README section 1 now links it as the actual demo entry point
  instead of describing a file that only existed locally.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

(none - the dashboard is an application built on top of the package's existing
`get_financial_data()`/`compute_*()` surface, not part of the `data-retrieval`
capability itself; see README section 3's 2026-11-01 note. No package function
signature or return contract changed.)

## Impact

- `dashboard/`: new directory, see above.
- `docs/dashboard.html`: new generated file (committed output, matching
  `docs/review.html`/`compare.html`'s existing convention of committing a static
  snapshot rather than requiring a live build step to view the demo).
- `README.md`: section 1 updated to point at the committed, repository-hosted
  dashboard and to describe the disagreement-surfacing behavior; no scope change.
- `AGENTS.md` / `PLANNING_LOG.md`: dated entries recording this change and why it
  was needed (code review feedback, not a self-discovered gap).
- No change to `data_acquisition/reconcile.py`, `CONCEPT_MAP`, or any test file -
  the package's own return contract (`get_financial_data()` still returns every row
  untouched) is exactly what makes this fix possible without touching the package.
