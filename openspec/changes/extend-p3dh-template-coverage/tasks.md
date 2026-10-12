# Tasks

## 1. Configuration

- [x] 1.1 Scrape the live P3DH Template slicer's full option list (depends on: P3DH
      scraper) and write every real data template (excluding the "Select all" UI
      control and the `X_01.00` contact-person metadata template) to
      `data/modules.txt` - verify by loading it via `run_update._load_modules()`
      and confirming the count matches the scraped list
      - 2026-10-12: done ahead of this change - 114 templates written, confirmed
        loading cleanly. See PLANNING_LOG.md/DATA_SOURCES_NOTES.md 2026-10-12.

## 2. Inspect candidate templates (depends on: P3DH scraper)

- [ ] 2.1 Fetch (or reuse a cached export of) EU OV1 (`K_60.00`) for Erste Group
      Bank AG; open it directly with openpyxl and record whether its `Row` column
      carries a real EBA code or is empty - verify by writing the finding to
      DATA_SOURCES_NOTES.md with the actual row codes/names observed
- [ ] 2.2 Do the same for the EU CQ-series (`K_80.00`-`K_87.00`) - at least one
      template from this series, for the same sample bank - verify the same way
- [ ] 2.3 Do the same for EU CC1 (`K_66.01`, composition of regulatory own funds)
      - verify the same way
- [ ] 2.4 For any candidate whose `Row` column is empty/per-filer, repeat the
      inspection for one more bank (mirroring the EU LI1 BNP Paribas check) before
      concluding it's LI1-shaped rather than assuming from one bank alone - verify
      by recording both banks' findings together

## 3. Decide and wire

- [ ] 3.1 For each candidate confirmed KM1-shaped (fixed row codes), add its clean,
      template-defined rows to `reconcile.CONCEPT_MAP` following the existing
      `"<template>::Row=<code>::<column>"` item-code format - verify by a new test
      in `tests/test_reconcile.py` asserting `status == "ok"` and a plausible value
      range for each new concept, against Erste's cached export
- [ ] 3.2 For each candidate confirmed per-filer/LI1-shaped, or otherwise too
      ambiguous to map safely, explicitly document the exclusion (which fields were
      checked, why it doesn't qualify under the new data-retrieval requirement) in
      `reconcile.py`'s module docstring and DATA_SOURCES_NOTES.md - verify by
      checking neither module's docstring nor `CONCEPT_MAP` leaves the template
      unaddressed (either wired, or excluded-with-reason, never silently absent)
- [ ] 3.3 If any newly-mapped concept has an independent cross-check available (a
      stress_test or ESEF figure for the same real-world quantity, as EU KM1's
      cet1_capital/cet1_ratio had), perform that cross-check before trusting the
      mapping, the same way the 2026-10-11 EU KM1 wiring did - verify by recording
      the specific compared values and their relative gap

## 4. Small-sample validation fetch (depends on: P3DH scraper)

- [ ] 4.1 For each newly-wired template, fetch it for 2-3 sample pilot banks
      (Erste, plus one bank with strong EU LI1 coverage and one with weak
      coverage) across the currently-expected waves, before committing to a
      full-pilot fetch - verify via `reconcile.get_financial_data()` returning
      real `p3dh` rows (status `ok` or correctly-reasoned `missing_from_source`)
      for each sample bank

## 5. Full pilot acquisition (depends on: P3DH scraper)

- [ ] 5.1 Decide, per newly-wired template, whether the small-sample result
      justifies a full 46-bank fetch - verify by a one-line decision recorded in
      PLANNING_LOG.md per template (fetch fully / not worth it, and why)
- [ ] 5.2 Run `run_update.py` (optionally in `--limit`-sized chunks across several
      invocations, given the real multi-day scale) for every template approved in
      5.1, across the full pilot sample - verify via `data/state/download_log.json`
      success/failure counts and the run's own failure-type breakdown (task 1.4)
- [ ] 5.3 Spot-check `reconcile.get_financial_data()` for a handful of banks across
      the newly-fetched templates - verify real, plausible `p3dh` rows come back,
      not just successful file downloads

## 6. Close out

- [ ] 6.1 Update `AGENTS.md`'s P3DH section and "Possible next steps" to reflect
      whichever templates ended up wired vs. excluded - verify by re-reading the
      updated section against `reconcile.CONCEPT_MAP`'s actual contents
- [ ] 6.2 Once 2-5 are complete and `openspec validate extend-p3dh-template-coverage
      --strict` passes, archive the change - verify via `openspec archive` and the
      resulting `openspec/specs/data-retrieval/spec.md` containing the new
      concept-mapping requirement
