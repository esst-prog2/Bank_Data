# Tasks: Add MVP v1

## 1. Data sources (prerequisite — see AGENTS.md "Immediate next steps")

- [x] 1.1 Verify `data_acquisition/edap_scraper.py` against the live P3DH page
      (`--headed`, `playwright codegen` pass); resolve the Entity-slicer (LEI vs.
      display name) and Module/Template list open questions
      — 2026-10-06: verified headlessly (network access to edap-public.eba.europa.eu
      and app.powerbi.com turned out to be available from this session, unlike the
      2026-09-19 attempt). Entity slicer takes a display/legal name, not an LEI
      (LEI search returns 0 results). Module and Template are genuinely different
      lists, cross-filtered by Power BI - Module doesn't need to be set at all once
      Template is. Real selectors captured from the live DOM (aria-labels differ
      from visible header text for 2 of 4 fields; search requires real keystrokes
      via `.type()`, not `.fill()`; Escape doesn't close a popup, re-clicking the
      trigger does; the real export control is the table visual's own `.vcMenuBtn`
      context menu, not the page-level `#exportFileButton`). Full end-to-end run
      confirmed twice independently: Erste Group Bank AG, EU KM1 template,
      31/12/2025 -> a real, structured 198-row .xlsx. Also found P3DH's available
      reference dates only go back to 30/06/2025 - it cannot reproduce the spike's
      FY2024 comparison. `edap_downloader.fetch_module()` now calls the verified
      scraper for real instead of raising `BulkAccessNotConfirmed` unconditionally.
      See `edap_scraper.py`'s docstring and DATA_SOURCES_NOTES.md's 2026-10-06
      entry for the full trail.
- [x] 1.2 Populate `data/entities.csv` from a real EBA Transparency Exercise
      participant list, trimmed to the pilot banks v1 will support. Once 1.1
      is verified, cross-check this list against the P3DH Entity slicer's own
      discovered entities and flag mismatches — the Transparency Exercise
      participant list is a proxy, not confirmed ground truth for who's live
      on P3DH (per EBA's 2026-09-22 reply, DATA_SOURCES_NOTES.md)
      — 2026-09-25: populated from the EBA Stress Test 2025 participant list
      instead (64 real, LEI-tagged banks) after finding the 2025 Transparency
      Exercise landing page (`eu-wide-transparency-exercise-0`) doesn't link
      individual per-bank result PDFs the way `_PARTICIPANT_LINK_RE` expects
      (`discover_participants("transparency", 2025)` returns 0 — a real gap,
      not yet fixed; see DATA_SOURCES_NOTES.md). Cross-check against P3DH's
      own Entity slicer is still pending 1.1.
      — 2026-10-06: trimmed using S&P's top-50 European banks by assets (2026)
      as the external criterion: 13 of 50 excluded as outside EBA's remit
      (UK/Switzerland/Russia/Turkiye), the remaining 37 EU/EEA banks all
      matched an entity already in the 64-bank list (names resolved via
      GLEIF, 2 corrupted LEIs in EBA's own source data fixed — see
      DATA_SOURCES_NOTES.md). `entities.csv` now has `sp50_2026_rank` marking
      which 37 of the 64 are in that external top-50 sample, kept alongside
      the other 27 rather than deleted, so a pilot run can filter to the
      smaller set without losing the discovered universe.
- [x] 1.3 Create `data/modules.txt` with the exact disclosure module/template
      codes the pilot banks submit
      — 2026-10-07: full 37-bank pilot sample run completed (592 combinations:
      37 banks x 2 templates x up to 8 waves) - 364 successes (61.5%), 1.1GB
      of real P3DH data cached. 34 of 37 banks have at least some real data.
      Getting here required fixing real entity-matching bugs in
      `edap_scraper.py` (GLEIF legal names vs. P3DH's own display text differ
      in case, punctuation, and legal-form language variants - see
      DATA_SOURCES_NOTES.md's 2026-10-06/07 entries), not just running the
      script - entity-match coverage went from 15/37 to 34/37 as a result.
      Only 2 templates are covered (EU KM1, EU LI1) - still not the full
      ~100+ P3DH lists, but both are now genuinely exercised across the whole
      pilot sample rather than one bank. Remaining gaps (3 banks entirely
      absent/misidentified; EU LI1's confirmed semi-annual/annual-only
      frequency; per-bank submission-timing differences) are each checked
      and explained, not unexplained failures - see DATA_SOURCES_NOTES.md.
- [x] 1.4 In `run_update.py`'s state tracking, distinguish a wave that hasn't
      published yet (`not_yet_published`) from a genuine retrieval failure —
      currently both fall into the same generic `except Exception` branch and
      are recorded as `status: "failed"`. EBA confirmed the T+4/6/8 calendar
      is an expectation, not a guarantee (DATA_SOURCES_NOTES.md, 2026-09-22),
      so late-but-expected waves will be routine and shouldn't be conflated
      with an actually broken scraper
      — 2026-10-06: now has concrete real-world motivation beyond the EBA
      calendar case - the first live run found two more genuinely-distinct
      "failed" causes (an entity simply absent from P3DH's own list; a
      template not disclosed at a given reference date's frequency) that are
      currently indistinguishable from a real scraper break in
      `download_log.json` without reading the full error string by hand.
      — 2026-10-11: implemented `run_update._classify_failure()`, keyed off the
      specific exception type/message each cause actually produces (see that
      function's docstring): `config_missing_entity` (LEI not in
      `entities.csv`), `entity_not_found_on_p3dh` (Entity slicer had no match),
      `template_or_date_not_available` (Template or Reference date slicer had
      no match - deliberately NOT split further into "not yet published" vs.
      "doesn't disclose at this frequency", since both produce the identical
      symptom and there's no reliable way to tell them apart from the error
      alone; a `days_overdue` figure is recorded instead as a human-readable
      hint), and `scraper_error` (anything else - the only bucket that should
      actually alarm an operator). Each `download_log.json` failure entry now
      carries `failure_type` and `days_overdue`; the run's own summary log
      prints an all-time failure-type breakdown. Tests in
      `tests/test_run_update.py` pin all four buckets against the real
      exception shapes `fetch_module()`/`edap_scraper._select_slicer()` raise.
      Decided and carried out by agent.
- [x] 1.5 Confirm none of the v1 pilot banks report on a non-December fiscal
      year-end. `waves.py`'s `_reference_dates_since()` only generates
      YEAR_END/YEAR_END_REMUNERATION waves for December reference dates, but
      EBA's FAQ B2 confirms non-December year-ends are also expected at
      "reference date + 6/8 months" (DATA_SOURCES_NOTES.md, 2026-09-22). If
      any pilot bank has one, extend `waves.py` to generate a YEAR_END wave
      for that bank's actual fiscal year-end month, not just December
      — 2026-10-11: checked directly against filings.xbrl.org (ground truth -
      real filed `period_end` values, not our own Dec-31 assumption) for all
      37 `sp50_2026_rank` pilot banks. Result: zero non-December `period_end`
      values found anywhere in the 31 banks that have any indexed ESEF data at
      all (every value is `*-12-31`); the other 6 (Deutsche Bank, Commerzbank,
      DZ Bank, LBBW, Bayerische Landesbank, Confederation Nationale Credit
      Mutuel) have zero filings indexed - the pre-existing, separately
      documented German/Credit Mutuel gap (AGENTS.md), not a fiscal-year-end
      issue. Confirmed: the Dec-31-only assumption in `waves.py` and
      `esef_client.py` is not a real limitation for any v1 pilot bank, based on
      actual filed data rather than documentation. No code change needed.
      Decided and carried out by agent.

## 2. Package surface

- [x] 2.1 Define the public function signature: bank identifier, reporting
      period, requested variables -> pandas DataFrame
      — 2026-09-25: `data_acquisition.reconcile.get_financial_data(bank_lei,
      concepts, period=None)`; `period=None` returns every period/scenario
      the source has, which is how a reported-actual and a scenario-projected
      figure for the same concept end up in one call.
- [x] 2.2 Define the DataFrame's columns: value, source reporting item,
      standardized concept, comparability flag/reason, missing-vs-failed status
      — 2026-09-25: implemented exactly as design.md decision 3's schema
      (`bank_lei, period, standardized_concept, source_reporting_item, source,
      provenance, value, status, origin_reference`).

## 3. Reconciliation logic

- [x] 3.1 Build the source-item -> standardized-concept mapping for the pilot
      banks' variables
      — 2026-09-25: `reconcile.CONCEPT_MAP`, 5 concepts (CET1 ratio, CET1
      capital, total risk exposure amount, net interest income, profit/loss
      for the year) from the Stress Test 2025 TRA_SUM template, sourced from
      that download's own `Data_Dictionary.xlsx`. Extended same day to add
      `data_acquisition/esef_client.py` (ESEF via filings.xbrl.org — real,
      confirmed working for Erste Group Bank AG's FY2024 filing) with 2 more
      concepts (total assets, total equity) plus the *same* net interest
      income / profit-or-loss concepts as the stress test, from IFRS taxonomy
      tags.
      — 2026-10-11: wired in P3DH's EU KM1 template too (`reconcile._p3dh_rows`),
      a third source, reusing cet1_capital/cet1_ratio/total_risk_exposure_amount
      - cache-only (reads what `run_update.py` has already fetched; never a live
      P3DH query from inside this module - see that function's docstring for
      why). EU LI1 (also scraped) deliberately not wired in - it's a scope-
      reconciliation table, not simple concept:value facts.
- [x] 3.2 Implement provenance tagging (reported actual vs.
      scenario-projected) and source traceability so every figure can be
      checked against its origin, including when multiple sources report the
      same concept
      — 2026-09-25: see design.md decision 2's revised, scenario-code-scoped
      table and `reconcile._SCENARIO_PROVENANCE`.
- [x] 3.3 Distinguish "missing from source" from "retrieval/processing failed"
      end to end (acquisition layer already raises loudly per AGENTS.md's
      working conventions — surface that distinction through to the DataFrame)
      — 2026-09-25: `status: "missing_from_source"` row vs. `DataSourceError`
      raised (never returned as a row) in `reconcile.py`.

## 4. Verification (see proposal's acceptance criteria / README section 4)

- [x] 4.1 Test: given a supported bank + period + available variable, the
      returned value has correct source item and standardized-concept mapping
      — `tests/test_reconcile.py::test_supported_bank_period_and_variable_returns_value_and_mapping`
- [x] 4.2 Test: given a variable genuinely absent from source, it's identified
      as missing-from-source, not as a retrieval/processing failure
      — `tests/test_reconcile.py::test_variable_absent_for_period_is_missing_not_failed`
      and `::test_retrieval_failure_is_raised_not_returned_as_missing`
- [x] 4.3 Test: given two figures from different sources for the same
      bank/period/concept (e.g. a reported actual and a stress-test scenario
      projection), each is tagged with its provenance and neither is
      combined into a single value
      — `tests/test_reconcile.py::test_reported_actual_and_scenario_projection_both_returned_untagged_as_one`,
      `::test_two_independent_sources_report_same_concept_untagged_as_one` (ESEF),
      and (2026-10-11) `::test_p3dh_and_stress_test_both_returned_untagged_as_one` (P3DH).
- [x] 4.4 Archive this change into `openspec/specs/data-retrieval/` once the
      above pass
      — 2026-10-11: unblocked. 1.1/1.3 were already done by 2026-10-07; 1.4/1.5
      closed out 2026-10-11 (see section 1 above); P3DH is now wired into
      `reconcile.py` (EU KM1 only - deliberately re-scoped, not deferred: the
      user chose "EU KM1 only" over also wiring EU LI1, 2026-10-11, since LI1
      is a structurally different reconciliation table and was never actually
      required by README section 3's MVP scope - the shape ("regulatory"
      broadly) was already satisfied by the stress test). Archived.
