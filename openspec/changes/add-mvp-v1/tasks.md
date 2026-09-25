# Tasks: Add MVP v1

## 1. Data sources (prerequisite — see AGENTS.md "Immediate next steps")

- [ ] 1.1 Verify `data_acquisition/edap_scraper.py` against the live P3DH page
      (`--headed`, `playwright codegen` pass); resolve the Entity-slicer (LEI vs.
      display name) and Module/Template list open questions
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
- [ ] 1.3 Create `data/modules.txt` with the exact disclosure module/template
      codes the pilot banks submit
- [ ] 1.4 In `run_update.py`'s state tracking, distinguish a wave that hasn't
      published yet (`not_yet_published`) from a genuine retrieval failure —
      currently both fall into the same generic `except Exception` branch and
      are recorded as `status: "failed"`. EBA confirmed the T+4/6/8 calendar
      is an expectation, not a guarantee (DATA_SOURCES_NOTES.md, 2026-09-22),
      so late-but-expected waves will be routine and shouldn't be conflated
      with an actually broken scraper
- [ ] 1.5 Confirm none of the v1 pilot banks report on a non-December fiscal
      year-end. `waves.py`'s `_reference_dates_since()` only generates
      YEAR_END/YEAR_END_REMUNERATION waves for December reference dates, but
      EBA's FAQ B2 confirms non-December year-ends are also expected at
      "reference date + 6/8 months" (DATA_SOURCES_NOTES.md, 2026-09-22). If
      any pilot bank has one, extend `waves.py` to generate a YEAR_END wave
      for that bank's actual fiscal year-end month, not just December

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
      tags. P3DH is still not wired in.
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
      — `tests/test_reconcile.py::test_reported_actual_and_scenario_projection_both_returned_untagged_as_one`
- [ ] 4.4 Archive this change into `openspec/specs/data-retrieval/` once the
      above pass
      — not done: 1.1/1.3/1.4/1.5 (P3DH scraper verification, modules.txt,
      run_update.py's not-yet-published distinction, non-December fiscal
      year-ends) are still open, and only one source (eba_stress_test) is
      wired into `reconcile.py` so far — deferred past this session's
      deadline-driven scope on purpose (see AskUserQuestion confirmation,
      2026-09-25). Archive once those are addressed or the change is
      re-scoped to drop them.
