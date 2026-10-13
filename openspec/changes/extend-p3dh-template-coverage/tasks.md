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

- [x] 2.1 Fetch (or reuse a cached export of) EU OV1 (`K_60.00`) for Erste Group
      Bank AG; open it directly with openpyxl and record whether its `Row` column
      carries a real EBA code or is empty - verify by writing the finding to
      DATA_SOURCES_NOTES.md with the actual row codes/names observed
      - 2026-10-12: confirmed KM1-shaped - 34 fixed, globally-unique row codes
        (e.g. "0010" = "01. Credit risk (excluding CCR)", "0380" = "29. Total").
        See DATA_SOURCES_NOTES.md's 2026-10-12 (third) entry.
- [x] 2.2 Do the same for the EU CQ-series (`K_80.00`-`K_87.00`) - at least one
      template from this series, for the same sample bank - verify the same way
      - 2026-10-12: inspected EU CQ3 (`K_82.00`). Row codes are NOT globally
        unique (reused across 3 internal sub-sheets) - see 2.4.
- [x] 2.3 Do the same for EU CC1 (`K_66.01`, composition of regulatory own funds)
      - verify the same way
      - 2026-10-12: confirmed KM1-shaped (94 fixed, globally-unique row codes,
        single Open Key=None throughout) but deliberately not wired - see 3.2.
- [x] 2.4 For any candidate whose `Row` column is empty/per-filer, repeat the
      inspection for one more bank (mirroring the EU LI1 BNP Paribas check) before
      concluding it's LI1-shaped rather than assuming from one bank alone - verify
      by recording both banks' findings together
      - 2026-10-12: EU CQ3's `Row` codes repeat per sub-sheet (on-balance,
        off-balance, grand-total - disambiguated by the `Cell` field's own
        ".a"/".b"/".c" prefix), but `Row Name` itself ("220 Total" etc.) is
        still a fixed, bank-independent EBA caption - confirmed identical
        wording on BNP Paribas's own export before trusting it. Not LI1-shaped
        after all; safely mappable via `Row Name` instead of `Row`.

## 3. Decide and wire

- [x] 3.1 For each candidate confirmed KM1-shaped (fixed row codes), add its clean,
      template-defined rows to `reconcile.CONCEPT_MAP` following the existing
      `"<template>::Row=<code>::<column>"` item-code format - verify by a new test
      in `tests/test_reconcile.py` asserting `status == "ok"` and a plausible value
      range for each new concept, against Erste's cached export
      - 2026-10-12: wired EU OV1 (credit_risk_rwa, counterparty_credit_risk_rwa,
        cva_risk_rwa, market_risk_rwa, operational_risk_rwa, plus row 0380 into
        the existing total_risk_exposure_amount concept) and EU CQ3
        (performing_exposures, non_performing_exposures, via `Row Name=` instead
        of `Row=` - no code change needed, `_read_p3dh_fact` was already generic
        over any header column). Added `compute_npl_ratio()`. 4 new tests, all
        passing (`test_p3dh_ov1_rwa_breakdown_concepts_are_new`,
        `test_p3dh_ov1_total_rwa_is_untagged_as_one_with_km1s_own_total`,
        `test_p3dh_cq3_matches_by_row_name_not_ambiguous_row_code`,
        `test_compute_npl_ratio_matches_hand_calculation`,
        `test_compute_npl_ratio_raises_when_not_cached`).
- [x] 3.2 For each candidate confirmed per-filer/LI1-shaped, or otherwise too
      ambiguous to map safely, explicitly document the exclusion (which fields were
      checked, why it doesn't qualify under the new data-retrieval requirement) in
      `reconcile.py`'s module docstring and DATA_SOURCES_NOTES.md - verify by
      checking neither module's docstring nor `CONCEPT_MAP` leaves the template
      unaddressed (either wired, or excluded-with-reason, never silently absent)
      - 2026-10-12: EU CC1 excluded - confirmed KM1-shaped (not ambiguous), but
        its 94 rows are a detailed capital-adjustment breakdown that would need
        its own curation pass to pick which rows matter, the same reason most of
        LI1's ~60 line items stayed unwired. Documented in reconcile.py's module
        docstring and DATA_SOURCES_NOTES.md.
- [x] 3.3 If any newly-mapped concept has an independent cross-check available (a
      stress_test or ESEF figure for the same real-world quantity, as EU KM1's
      cet1_capital/cet1_ratio had), perform that cross-check before trusting the
      mapping, the same way the 2026-10-11 EU KM1 wiring did - verify by recording
      the specific compared values and their relative gap
      - 2026-10-12: EU OV1's row 0380 ("29. Total") cross-checked against EU
        KM1's own TREA total for the same bank/period - they do NOT match
        (149,673.86 vs. 147,487.07 EUR m, ~1.5% gap). Mapped to the same
        total_risk_exposure_amount concept anyway (per this module's own
        untagged-as-one rule) rather than treated as a mapping error - the gap
        itself is the real finding, not yet explained, recorded as such rather
        than silently reconciled. EU CQ3's NPL ratio cross-checked for
        plausibility (no independent source exists for it): Erste ~1.42%, BNP
        Paribas ~1.51%, both in the normal range for a strong European bank.

## 4. Small-sample validation fetch (depends on: P3DH scraper)

- [x] 4.1 For each newly-wired template, fetch it for 2-3 sample pilot banks
      (Erste, plus one bank with strong EU LI1 coverage and one with weak
      coverage) across the currently-expected waves, before committing to a
      full-pilot fetch - verify via `reconcile.get_financial_data()` returning
      real `p3dh` rows (status `ok` or correctly-reasoned `missing_from_source`)
      for each sample bank
      - 2026-10-12: fetched for Erste, BNP Paribas, HSBC Continental Europe
        (weak EU LI1 coverage) across all 4 currently-expected reference
        dates - 35 successes, 13 failures (all template_or_date_not_available).
        Verified real `ok` p3dh rows for credit_risk_rwa/performing_exposures
        for all 3 banks. See PLANNING_LOG.md 2026-10-12.

## 5. Full pilot acquisition (depends on: P3DH scraper)

- [x] 5.1 Decide, per newly-wired template, whether the small-sample result
      justifies a full 46-bank fetch - verify by a one-line decision recorded in
      PLANNING_LOG.md per template (fetch fully / not worth it, and why)
      - 2026-10-12: both approved. EU OV1 - strong coverage (Erste 4/4 dates,
        BNP 3/4, HSBC 2/4). EU CQ3 - sparser (mostly the 2025-12-31 annual
        date per bank) but real and worth fetching fully regardless.
- [x] 5.2 Run `run_update.py` (optionally in `--limit`-sized chunks across several
      invocations, given the real multi-day scale) for every template approved in
      5.1, across the full pilot sample - verify via `data/state/download_log.json`
      success/failure counts and the run's own failure-type breakdown (task 1.4)
      - 2026-10-13: ran the full 46-bank x 2-template fetch. Hit a genuine
        environment outage mid-run (net::ERR_INTERNET_DISCONNECTED, confirmed via
        the raw exception text, not assumed) - retried after connectivity was
        restored, since the idempotent state file only skips "success" entries.
        Final result: 485 successes, 251 failures, ALL cleanly explained
        (203 template_or_date_not_available, 48 entity_not_found_on_p3dh) - the
        12 transient scraper_error timeouts from the retry were individually
        re-fetched and now correctly reclassified. Zero unexplained failures.
- [x] 5.3 Spot-check `reconcile.get_financial_data()` for a handful of banks across
      the newly-fetched templates - verify real, plausible `p3dh` rows come back,
      not just successful file downloads
      - 2026-10-13: spot-checked 6 random pilot banks (Banco BPM, KBC, DZ Bank,
        Rabobank, Nykredit, Intesa Sanpaolo) for credit_risk_rwa/
        performing_exposures/total_risk_exposure_amount - all returned real `ok`
        or correctly-reasoned `missing_from_source` p3dh rows, no crashes.

## 6. Close out

- [ ] 6.1 Update `AGENTS.md`'s P3DH section and "Possible next steps" to reflect
      whichever templates ended up wired vs. excluded - verify by re-reading the
      updated section against `reconcile.CONCEPT_MAP`'s actual contents
- [ ] 6.2 Once 2-5 are complete and `openspec validate extend-p3dh-template-coverage
      --strict` passes, archive the change - verify via `openspec archive` and the
      resulting `openspec/specs/data-retrieval/spec.md` containing the new
      concept-mapping requirement
