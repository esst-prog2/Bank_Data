# Tasks

- [x] Locate the dashboard HTML, precompute script, and every input file they
      depend on (they existed only on the user's Desktop / a prior session's
      scratchpad, never in the repository).
- [x] Move the precompute script (`build_comparison_data.py`) and the HTML
      assembly script (`build_dashboard.py`) into a new `dashboard/` directory in
      the repository, with every input (`pilot_28_leis.json`, `total_assets.json`,
      `europe_map.svg`, `bank_logos/`, `country_flags/`) committed alongside them.
- [x] Fix the absolute `file:///`-path dependency on logos/flags found while doing
      so: inline every image as a base64 data URI so the generated HTML has no
      external file dependencies.
- [x] Check, across all 28 pilot banks, whether `total_risk_exposure_amount`'s
      EU KM1 vs EU OV1 figures disagree anywhere besides Erste Group (they do, for
      one more bank, confirming this is a real recurring case worth handling
      generically rather than hardcoding Erste as a special case).
- [x] Add disagreement detection to `pick_best_row()`, scoped to the
      `reported_actual` provenance tier only (excluding EBA stress-test
      baseline/adverse scenario pairs, which differ by design and are not a
      genuine disagreement).
- [x] Render disagreement cells distinctly in the results table (every value shown,
      hover tooltip with sources and the percentage gap), excluded from "best
      value" highlighting.
- [x] Regenerate `dashboard/comparison_data.json` and `docs/dashboard.html` from the
      committed scripts and verify the Erste Group row now shows both figures.
- [x] Update `README.md` section 1 to point at the committed dashboard; update
      `AGENTS.md`/`PLANNING_LOG.md` with dated entries.
- [x] Verify the regenerated dashboard end to end (basket selection, concept
      picker, results table including the disagreement cell, CSV export) before
      committing.
