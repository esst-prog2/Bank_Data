# European Bank Financial Data Reconciliation — agent memory

Context for whichever AI coding agent picks this up next (this file is the portable
project-memory file most agents — Claude Code, Codex, Cursor, OpenSpec, and others —
read automatically on startup in this directory). Read `README.md` first (the actual
pitch/spec), then `DATA_SOURCES_NOTES.md` (the full research trail with sources) —
this file is the short version: what's decided, what's built, what's still open.

## Planning log

Whenever we decide something about this project — a requirement, a number, a name,
a tool — append one line to PLANNING_LOG.md: the date, what was decided, and whether
I (the agent) decided it or the user did. Never rewrite an earlier line.

## What this project is

A Python package that, given a bank + reporting period + requested variables, retrieves
matching figures from financial-statement (ESEF) and regulatory (Pillar 3 / stress test /
transparency exercise) sources, maps them to standardized concepts, and flags what's
genuinely non-comparable rather than silently combining it. Returns a pandas DataFrame.
Scope for v1 (see README section 3) is a handful of supported, publicly traded banks, not
full EU coverage. "Publicly traded" is ESEF's own constraint, not a choice made here: the
EU Transparency Directive requires ESEF filings only from issuers with securities (shares
or bonds) admitted to trading on an EU regulated market - confirmed 2026-10-28 via the
cases already in `entities.csv` (e.g. Credit Industriel et Commercial, tracked specifically
because it's "the group's main **listed** banking subsidiary," per the 2026-10-07 entry in
DATA_SOURCES_NOTES.md, not the unlisted Credit Mutuel confederation itself). P3DH and the
EBA exercises are NOT restricted this way - they cover every significant supervised
institution regardless of listing status, which is why a few tracked pilot banks (e.g.
Cooperatieve Rabobank, DZ Bank, OP Osuuskunta) have real P3DH/stress-test data without
necessarily being equity-listed themselves.

## Data sources decided so far

Goal right now (per the user, 2026-09-17): as complete a compilation of publicly available
data as practical; which sources actually make the cut is deferred to later. Currently wired
up or in progress:

- **EBA Pillar 3 Data Hub (P3DH)** - live regulatory disclosures, launched Jan 2026. No
  public bulk API found (confirmed by direct inspection - it's an anonymous-access Power BI
  embed). Emailed P3DH@eba.europa.eu asking about bulk/API access; EBA replied 2026-09-22:
  bulk download/API access is "currently ongoing" discussion internally, with no commitment
  or timeline either way - **resolved 2026-10-12: EBA has nothing further to offer, no bulk
  access is coming.** The Playwright UI scraper (`data_acquisition/edap_scraper.py`) is
  therefore the permanent P3DH access method, not a stopgap pending a reply - verified end to end
  2026-10-06 (real filter selection, navigation, export, download) and exercised across the
  full 46-bank pilot sample (task 1.3). Its output is wired into
  `reconcile.get_financial_data()` as a third source (`reconcile._p3dh_rows`), cache-only -
  reading whatever `run_update.py` has already fetched, never a live P3DH query from inside
  `reconcile.py` (see that function's docstring for why). `data/modules.txt` lists all 114
  real P3DH templates (scraped 2026-10-12), but only 4 are actually wired - each inspected
  against a real export first, per `extend-p3dh-template-coverage`'s own rule (now also a
  `data-retrieval` spec requirement: never map a concept from a label that isn't the same,
  bank-independent identifier for every filer):
  - **EU KM1** (2026-10-11/12) - cet1_capital/tier1_capital/total_capital/cet1_ratio/
    total_risk_exposure_amount/leverage_ratio/liquidity_coverage_ratio/nsfr_ratio, using
    fixed, EBA-standardized row codes.
  - **EU LI1** (2026-10-12) - only its two clean TOTAL rows (Total Liabilities, Total
    shareholders' equity), giving total_equity a third source plus 3 new concepts
    (total_equity_prudential_scope, total_liabilities, total_liabilities_prudential_scope).
    **These are far sparser than they first looked**: checked 2026-10-13 against all 36
    cached exports (not just the 2-bank Erste/BNP Paribas check) - only 1/36 (Erste) has
    BOTH Open Keys at all; expect `missing_from_source` for roughly 35 of 36 pilot banks on
    the 3 P3DH-only concepts. LI1's other ~60 line items stay unwired - no Open Key label
    comes anywhere close to full-pilot coverage either (confirmed systematically, not
    assumed).
  - **EU OV1** (2026-10-12) - 5 new RWA-by-risk-type concepts (credit/CCR/CVA/market/
    operational risk), plus its own TREA total mapped into the SAME total_risk_exposure_amount
    concept KM1 already provides - revealing a real, unexplained ~1.5% gap between the two
    independently-disclosed totals for the same bank/period, surfaced rather than reconciled.
  - **EU CQ3** (2026-10-12) - performing_exposures/non_performing_exposures, feeding
    `compute_npl_ratio()`. Its `Row` codes repeat across 3 internal sub-sheets - matched by
    `Row Name` instead (still bank-independent, confirmed across 2 banks).
  - **EU CC1** was inspected twice (2026-10-12, 2026-10-13) and confirmed NOT worth wiring:
    its only clean headline rows exactly duplicate EU KM1's own figures (same COREP
    submission, not an independent cross-check), and its other ~90 rows are granular
    capital-deduction detail with no obvious curated subset.
  `data_acquisition/waves.py` encodes the EBA publication calendar (T+4/6/8 months per
  Article 4 of the ITS), but EBA also confirmed this is "an EBA expectation rather than a
  strict legal publication requirement" - so a wave being past its expected date is a
  normal, expected outcome, not a failure (see DATA_SOURCES_NOTES.md's 2026-09-22 entry).
- **EBA EU-wide Transparency Exercise** - real, confirmed bulk CSV, LEI-tagged, 2013-2025.
  Discontinued from June 2025 (EBA points to P3DH going forward) - frozen archive, good for
  reproducible test fixtures, not for anything ongoing. `data_acquisition/eba_exercises.py`.
- **EBA EU-wide Stress Test** - same structure, still active but biennial (2023, 2025, next
  ~2027). Figures are scenario-projected, NOT reported actuals - treat as non-comparable to
  Pillar 3/ESEF by default; this is a real instance of the README's own comparability risk.
  Same module as Transparency (`eba_exercises.py`, `exercise="stress_test"`).
- **ESEF financial-statement filings** - no single EU-wide repository yet (ESAP not live).
  `data_acquisition/esef_client.py` queries `filings.xbrl.org`'s JSON:API for one entity's
  own filings at a time - confirmed working 2026-09-25 for Erste Group Bank AG (Austria),
  which the earlier "well covered" guess (France, Italy, Spain, Netherlands) hadn't listed;
  that guess was from documentation, not a direct check. As of 2026-10-06, checked and
  fetched for all 37 S&P-ranked pilot banks in `entities.csv`: 29 have a FY2024 filing
  (cached under `data/raw/esef/`), 8 don't. **Germany is a confirmed NATIONAL gap on this
  aggregator, not a per-bank one**: `filings.xbrl.org`'s own `filter[country]=DE` returns
  zero filings total (vs. 1179 for France, 873 for Italy as of 2026-10-11) - no subsidiary
  LEI can fix this for Deutsche Bank, Commerzbank, DZ Bank, LBBW, or Bayerische Landesbank.
  Credit Mutuel's gap IS a subsidiary-LEI issue, and is fixed: its subsidiary Credit
  Industriel et Commercial (CIC, LEI `N4JDFKKH2FTD8RKFXO39`) has real ESEF filings
  FY2021-FY2024 and is now its own tracked pilot entity. Societe Generale (missing just
  FY2024) and Intesa Sanpaolo (missing FY2023 onward, corrected 2026-10-11 from an earlier
  understatement) are confirmed isolated filer-specific gaps under their own correct,
  ACTIVE/ISSUED LEIs - not subsidiary mismatches, not national gaps (France/Italy are both
  well covered). Ireland turned out fine (Bank of Ireland, AIB both have FY2024 filings) -
  the original "Ireland" flag was unconfirmed and is now resolved as a non-issue. Still
  can't discover "everyone reporting in country X" the way `eba_exercises.py` can for EBA's
  exercises, and only handles a calendar (Dec 31) fiscal year-end - confirmed (2026-10-11,
  task 1.5) not a live limitation for any of the 37 S&P-50 pilot banks: zero non-December
  `period_end` values found anywhere in `filings.xbrl.org`'s own filing records. See
  DATA_SOURCES_NOTES.md's 2026-10-06, 2026-10-07, and 2026-10-11 entries for the full
  per-bank breakdown and concept-coverage findings (net interest income and total equity
  are each genuinely untagged - not missing by bug - for several banks; see those entries
  before assuming `missing_from_source` there is wrong). **FY2025 filings are starting to
  appear** - found by accident 2026-10-12 (a test incidentally triggered a live fetch);
  checked deliberately 2026-10-13 (gap-esef-fy2025-check): 19/46 pilot banks have one
  indexed and cached now, the other 27 plausibly just haven't filed yet (4 of those are the
  German/Credit Mutuel national-gap entities).
- **GLEIF** - used only to enrich/validate an LEI you already have (legal name, country,
  status), never to discover which banks are in scope. `data_acquisition/gleif_client.py`.
- **Excluded**: ECB Supervisory Banking Statistics (SUP dataset) - checked directly,
  aggregated across all significant institutions only, no per-bank figures.

## Repo layout

```
data_acquisition/
    waves.py            - P3DH publication calendar -> "what's newly expected"
    entities.py         - loads/validates data/entities.csv (the tracked LEI universe)
    eba_exercises.py    - Transparency Exercise + Stress Test: discovery, download, entity extraction
    gleif_client.py     - GLEIF API wrapper (validation/enrichment only)
    edap_downloader.py  - swappable interface run_update.py calls; currently delegates to edap_scraper
    edap_scraper.py     - Playwright scraper for P3DH's Data Points Report - verified 2026-10-06
    esef_client.py      - ESEF filings via filings.xbrl.org's JSON:API (one entity/fiscal-year at a time)
    reconcile.py        - the package surface: get_financial_data() - concept mapping, provenance,
                          DataFrame schema; 3 sources wired (stress_test, esef, p3dh/EU KM1 only)
    run_update.py       - the script to schedule; idempotent, state-tracked in data/state/download_log.json;
                          failures carry a failure_type (see tasks.md 1.4)
data/
    entities.csv        - tracked banks (lei, name, country, sp50_2026_rank, pilot_added, notes) -
                          not committed empty, see .example; is_pilot = sp50_2026_rank OR pilot_added
    modules.txt          - P3DH Template option text to fetch per entity/period; since 2026-10-12
                          holds all 114 real templates (scraped directly from the live slicer,
                          not just EU KM1/EU LI1) - config only, not yet fetched at that scale
    raw/                - downloaded files land here, organized by source
    state/download_log.json - what's already been fetched, keyed by lei|wave|module
openspec/            - spec-driven development: specs/ (current behavior, now includes data-retrieval,
                       archived 2026-10-11), changes/ (proposals)
docs/
    review.html      - static snapshot of the MVP's output for the pilot bank; served via GitHub
                       Pages at https://esst-prog2.github.io/Bank_Data/review.html (Pages source:
                       main branch, /docs) - regenerate by hand from reconcile.py's output, this
                       is a snapshot, not a live app
DATA_SOURCES_NOTES.md  - full research trail: what was checked, what's confirmed, what's still open
requirements.txt
```

## Status

The `add-mvp-v1` change (README section 3's "first useful version") is DONE and archived
(2026-10-11, `openspec/changes/archive/2026-10-11-add-mvp-v1`, requirements now live in
`openspec/specs/data-retrieval/spec.md`). `get_financial_data()` returns real data from 3
wired sources (EBA Stress Test 2025, ESEF, P3DH's EU KM1 + partial EU LI1) across 15
standardized concepts, for a 46-bank pilot sample (the original 37 S&P-50 banks plus 9
added 2026-10-11 on their own documented merits - see `entities.csv`'s `pilot_added`
column). All 9 now have real P3DH data too (fetched 2026-10-12: 88 successes, 0 scraper
errors, 0 entity-matching failures - every one of the 9 banks' names resolved against
P3DH's Entity search on the first attempt). The EBA bulk-access question is also closed
(2026-10-12, confirmed by the user:
EBA has nothing further to offer) - the Playwright scraper is permanent, not a stopgap.
See PLANNING_LOG.md and DATA_SOURCES_NOTES.md for what was actually found at each step,
especially 2026-10-08 (BBVA/Sabadell data error), 2026-10-11 (P3DH/EU KM1 wiring,
ESEF-gap investigation), and 2026-10-12 (EU LI1 wiring, EU KM1 extended, a real
read_only/openpyxl row-trimming bug found via the test suite) entries.

## Closed change: extend-p3dh-template-coverage

Done and archived (`openspec/changes/archive/2026-10-13-extend-p3dh-template-coverage`).
EU OV1/EU CQ3 wired, EU CC1 inspected and excluded, full-pilot fetch done for both wired
templates, this file's P3DH section and `openspec/specs/data-retrieval/spec.md`'s own
concept-mapping requirement both updated to match. (Note 2026-10-27: that change's own
`tasks.md` still shows checkboxes 6.1/6.2 unticked - cosmetic, the archive folder and the
spec requirement confirm the work itself is done; archived files are a frozen record, not
re-edited.)

## Gap tasks (opened 2026-10-13, after reviewing what further data-gathering remained)

- **gap-esef-fy2025-check** - done. 19/46 pilot banks now have FY2025 ESEF data cached.
- **gap-li1-pilot-coverage** - done. 9/10 banks missing EU LI1 data are genuine P3DH
  absences/non-disclosures; 1 (Danske Bank A/S) was a real fetch gap, retried and fixed.
- **gap-li1-line-items** - done. Confirmed systematically (36 banks, not 2) that no more
  EU LI1 line items are safe to wire, and that even the 2 already-wired totals are far
  sparser than previously documented (1/36 banks has both).
- **gap-cc1-revisit** - done. EU CC1 confirmed not worth wiring (see above).
- **gap-p3dh-full-catalog** - closed, out of scope for the final submission
  (2026-10-27, user decision: MVP scope stands, don't expand past the README pitch).
  The full 114-template catalog was never part of what README section 3 commits to -
  it explicitly rules out "comprehensive coverage of every financial and regulatory
  variable." The 4 templates actually wired (KM1/LI1/OV1/CQ3) already cover the
  demo's real needs: confirmed 2026-10-27 that 37/46 pilot banks already have all 4
  cached, including both banks used in the demo (Erste, BNP Paribas). The other 110
  templates, fetched only for Erste (2026-10-20), stay unwired and unfetched for
  everyone else - no further P3DH scraping planned before the final.
- **gap-national-oam-coverage** - opened 2026-10-20, per user request (two-week
  gap priority: data coverage over the DuPont feature - see PLANNING_LOG.md). Surveyed
  all 30 EU/EEA national OAMs (ESMA's official list) as potential ESEF/XBRL sources
  beyond `filings.xbrl.org`, this project's only wired ESEF source today. Found that
  Germany's existing confirmed gap (0 filings via filings.xbrl.org) is that aggregator's
  own documented access limitation, not necessarily an absence of German ESEF data -
  Germany's OAM (unternehmensregister.de) hasn't yet been directly checked for real
  machine-readable access. Full findings, the complete OAM table, and open questions in
  DATA_SOURCES_NOTES.md's 2026-10-20 entry. **2026-10-21 update**: checked directly via
  Playwright - Germany's ESEF filings genuinely exist and are freely, registration-free
  searchable there (confirmed real FY2023/2024/2025 entries for Deutsche Bank AG), but
  the actual filing viewer is gated behind a real, named CAPTCHA (`fox-captcha`) -
  a deliberate anti-automation measure, unlike every other source this project has
  wired. Decided not to attempt to defeat it. **2026-10-27 decision (user)**: closed
  as a permanent, documented gap rather than a manual one-off download - user declined
  hand-downloading filings. Germany stays uncovered by `esef_client.py` for the same
  reason Societe Generale/Credit Agricole SA are absent from P3DH: a real, deliberate
  access control on the source's side, not a bug or an unexplored lead. No further
  work planned here. See DATA_SOURCES_NOTES.md's 2026-10-21 and 2026-10-27 entries.

## Working conventions established so far

- Every acquisition module raises loudly on failure rather than returning empty/partial data
  silently (see `edap_downloader.BulkAccessNotConfirmed` and `run_update.py`'s per-item
  try/except that records failures in the state file instead of swallowing them).
- Prefer discovering entity/LEI lists from a real EBA-published source (exercise participant
  lists) over guessing bank names against GLEIF.
- `DATA_SOURCES_NOTES.md` is the running research log - append to it (with a dated section)
  rather than editing past findings, so the reasoning trail stays intact for the coursework
  write-up.
