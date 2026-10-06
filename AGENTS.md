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
Scope for v1 (see README section 3) is a handful of supported banks, not full EU coverage.

## Data sources decided so far

Goal right now (per the user, 2026-09-17): as complete a compilation of publicly available
data as practical; which sources actually make the cut is deferred to later. Currently wired
up or in progress:

- **EBA Pillar 3 Data Hub (P3DH)** - live regulatory disclosures, launched Jan 2026. No
  public bulk API found (confirmed by direct inspection - it's an anonymous-access Power BI
  embed). Emailed P3DH@eba.europa.eu asking about bulk/API access; EBA replied 2026-09-22:
  bulk download/API access is "currently ongoing" discussion internally, with no commitment
  or timeline either way. Treat the Playwright UI scraper as the access method for the
  foreseeable future, not a stopgap - see `data_acquisition/edap_scraper.py` and its
  docstring for exactly what's verified vs. not. `data_acquisition/waves.py` encodes the
  EBA publication calendar (T+4/6/8 months per Article 4 of the ITS), but EBA also confirmed
  this is "an EBA expectation rather than a strict legal publication requirement" - so a
  wave being past its expected date is a normal, expected outcome, not a failure (see
  DATA_SOURCES_NOTES.md's 2026-09-22 entry).
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
  (cached, 706MB under `data/raw/esef/`), 8 don't - **Germany is now a confirmed gap, not a
  guess**: all 5 German pilot banks (Deutsche Bank, Commerzbank, DZ Bank, LBBW, Bayerische
  Landesbank) have zero filings indexed; Credit Mutuel (a cooperative confederation, likely
  filed under a different legal entity's LEI) is also missing entirely; Societe Generale
  and Intesa Sanpaolo are indexed but missing specifically the 2024 filing. Ireland turned
  out fine (Bank of Ireland, AIB both have FY2024 filings) - the original "Ireland" flag was
  unconfirmed and is now resolved as a non-issue. Still can't discover "everyone reporting
  in country X" the way `eba_exercises.py` can for EBA's exercises, and only handles a
  calendar (Dec 31) fiscal year-end (same assumption as `waves.py`, see task 1.5) - extend
  both together if a pilot bank needs otherwise. See DATA_SOURCES_NOTES.md's 2026-10-06
  entries for the full per-bank breakdown and concept-coverage findings (net interest
  income and total equity are each genuinely untagged - not missing by bug - for several
  banks; see that entry before assuming `missing_from_source` there is wrong).
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
    edap_scraper.py     - Playwright scraper for P3DH's Data Points Report (UNVERIFIED, see its docstring)
    esef_client.py      - ESEF filings via filings.xbrl.org's JSON:API (one entity/fiscal-year at a time)
    reconcile.py        - the package surface: get_financial_data() - concept mapping, provenance, DataFrame schema
    run_update.py       - the script to schedule; idempotent, state-tracked in data/state/download_log.json
data/
    entities.csv        - tracked banks (lei, name, country, notes) - not committed empty, see .example
    modules.txt          - disclosure module codes to fetch per entity/period (create before running run_update)
    raw/                - downloaded files land here, organized by source
    state/download_log.json - what's already been fetched, keyed by lei|wave|module
openspec/            - spec-driven development: specs/ (current behavior), changes/ (proposals)
docs/
    review.html      - static snapshot of the MVP's output for the pilot bank; served via GitHub
                       Pages at https://esst-prog2.github.io/Bank_Data/review.html (Pages source:
                       main branch, /docs) - regenerate by hand from reconcile.py's output, this
                       is a snapshot, not a live app
DATA_SOURCES_NOTES.md  - full research trail: what was checked, what's confirmed, what's still open
requirements.txt
```

## Immediate next steps (in likely order)

Steps 1-2 and 5-6 below (P3DH scraper verification, populating `entities.csv`, starting
ESEF, the reconciliation logic itself) are done - see DATA_SOURCES_NOTES.md's 2026-10-06
entries and PLANNING_LOG.md for what was actually found. What's left:

1. **Extend `data/modules.txt`** past its one current entry (EU KM1, for Erste only) to the
   other pilot banks and other templates `reconcile.py` might want - the real P3DH Template
   option text, not a short module code (see `edap_downloader.py`'s docstring for why the
   format changed). Then run `run_update.py` for a real pass and see what it actually does
   against live P3DH data for more than one bank/template.
2. **Decide what to do about the 8 pilot banks with no FY2024 ESEF coverage** (5 German
   banks + Credit Mutuel have no filing at all; Societe Generale and Intesa Sanpaolo are
   indexed but missing specifically 2024 - see DATA_SOURCES_NOTES.md's 2026-10-06 ESEF
   entry). Options: accept the gap as a real, documented limitation; try a different
   fiscal year for those two; or investigate whether Credit Mutuel/BPCE/Credit Agricole's
   pattern (consolidated group reported under a different legal entity's LEI than the one
   EBA lists) also applies here.
3. **If EBA replies** to the bulk-access email: implement Option A in `edap_downloader.py`
   (a real HTTP call), keep the scraper as a fallback rather than deleting it, and update
   `DATA_SOURCES_NOTES.md`.
4. Tasks 1.4 (not-yet-published vs. failed state in `run_update.py`) and 1.5 (non-December
   fiscal year-ends in `waves.py`) remain open and untouched - see tasks.md.
5. See `openspec/changes/add-mvp-v1/` for the current MVP change proposal, derived from
   README section 3 ("The size").

## Working conventions established so far

- Every acquisition module raises loudly on failure rather than returning empty/partial data
  silently (see `edap_downloader.BulkAccessNotConfirmed` and `run_update.py`'s per-item
  try/except that records failures in the state file instead of swallowing them).
- Prefer discovering entity/LEI lists from a real EBA-published source (exercise participant
  lists) over guessing bank names against GLEIF.
- `DATA_SOURCES_NOTES.md` is the running research log - append to it (with a dated section)
  rather than editing past findings, so the reasoning trail stays intact for the coursework
  write-up.
