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
  that guess was from documentation, not a direct check. Still can't discover "everyone
  reporting in country X" the way `eba_exercises.py` can for EBA's exercises, and only
  handles a calendar (Dec 31) fiscal year-end (same assumption as `waves.py`, see task 1.5) -
  extend both together if a pilot bank needs otherwise. Germany and Ireland remain flagged as
  known gaps in DATA_SOURCES_NOTES.md's original entry, unconfirmed either way.
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
DATA_SOURCES_NOTES.md  - full research trail: what was checked, what's confirmed, what's still open
requirements.txt
```

## Immediate next steps (in likely order)

1. **Verify `edap_scraper.py` against the real page.** Run it once with `--headed`, expect at
   least one slicer selector to need fixing via a local `playwright codegen` pass (see
   DATA_SOURCES_NOTES.md's 2026-09-19 entry for the exact command and what to look for).
   Also resolve two open questions the first run should answer: does the Entity slicer take
   an LEI or a display name, and are "Module" and "Template" the same list or two different
   ones (currently assumed the same in `edap_downloader.fetch_module()`, flagged with a
   comment).
2. **Populate `data/entities.csv` for real.** Easiest path: run
   `python -m data_acquisition.eba_exercises transparency 2025` to seed it from a real EBA
   participant list, then trim to whichever pilot banks v1 actually wants.
3. **Create `data/modules.txt`** with the exact disclosure module/template codes those pilot
   banks submit (check the Data Points Report's own "Module"/"Template" filter options once
   the scraper can see them) - `run_update.py` refuses to run without this file.
4. **If EBA replies** to the bulk-access email: implement Option A in `edap_downloader.py`
   (a real HTTP call), keep the scraper as a fallback rather than deleting it, and update
   `DATA_SOURCES_NOTES.md`.
5. **Start the ESEF side** - not begun yet. `filings.xbrl.org`'s API is the concrete starting
   point (see DATA_SOURCES_NOTES.md's original entry for details and known coverage gaps -
   Germany and Ireland aren't reliably indexed there).
6. Only once real data is flowing from at least one source: start on the actual reconciliation
   logic (source-item -> standardized-concept mapping, provenance tagging) - the README
   calls this out as the main technical risk, so it deserves real data to test against rather
   than being designed against assumptions.
7. See `openspec/changes/add-mvp-v1/` for the current MVP change proposal, derived from
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
