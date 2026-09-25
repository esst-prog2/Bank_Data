# Add MVP v1: retrieve and reconcile financial data for supported banks

## Why

The project currently has data-acquisition modules in progress (EBA Pillar 3 Data
Hub scraper, Transparency Exercise/Stress Test archive, GLEIF enrichment) but no
defined package surface and no reconciliation logic yet. README.md section 3
("The size") already defines what a first useful version must do; this proposal
turns that into an OpenSpec change so it can be tracked, tasked, and archived into
`openspec/specs/` once built.

## What Changes

- Define the package's public contract: given a bank identifier, a reporting
  period, and requested financial/regulatory concepts, return a pandas DataFrame
  with the requested values.
- Every returned value carries source and provenance metadata: which
  XBRL/ESEF or regulatory reporting item produced it, whether it is a
  reported actual or a scenario-projected figure, and which standardized
  concept it maps to.
- Every returned value is tagged with enough source and provenance metadata
  to be checked against the publication it came from. The package does not
  attempt to reconcile figures across different accounting standards or
  reporting frameworks into a single comparable value; when more than one
  wired-up source reports the same concept for a bank and period, each
  source's figure is returned tagged by its provenance rather than combined.
- Values genuinely absent from the source are distinguished from values that
  could not be retrieved or processed (a package/source failure).
- Coverage is intentionally narrow: a defined set of pilot banks and a defined
  set of variables, not comprehensive EU coverage — see the "Not this term"
  list in README.md section 3, which stays out of scope for this change.

## Impact

- Affected specs: `openspec/specs/data-retrieval/` (new capability)
- Affected code: `data_acquisition/*` (entity/period/variable resolution surface
  on top of the existing scraper/downloader modules), plus new reconciliation
  logic (source-item -> standardized-concept mapping, provenance tagging)
  called out in AGENTS.md's "Immediate next steps" #6 as the main technical risk.
- Depends on at least one data source being reliably wired up end-to-end first
  (see AGENTS.md steps 1-3: verify the P3DH scraper, populate `data/entities.csv`,
  create `data/modules.txt`) — this proposal defines the target contract, it does
  not assume the sources are already working.

## Later levels (future change requests — not scoped or spec'd here)

Deliberately left as a list, not specs, per this week's assignment. Each of these
is a candidate change request for a coming week, not part of `add-mvp-v1`:

- **Wire up P3DH for real**: verify `edap_scraper.py` against the live page
  (`--headed`, a `playwright codegen` pass), connect it to
  `edap_downloader.fetch_module()`, and create `data/modules.txt` (tasks 1.1/1.3,
  carried forward unfinished from this change).
- **Fix `run_update.py`'s not-yet-published vs. failed conflation** (task 1.4) and
  **extend `waves.py`/`esef_client.py` for non-December fiscal year-ends** (task
  1.5) once a pilot bank actually needs either.
- **Expand pilot bank coverage** beyond Erste Group Bank AG — pick the actual v1
  pilot set and re-run entities/ESEF/stress-test acquisition for each.
- **Fix Transparency Exercise 2025 entity discovery**: `discover_participants
  ("transparency", 2025)` currently returns 0 (a landing-page structure change);
  `entities.csv` is seeded from Stress Test 2025 instead as a workaround.
- **Broaden ESEF coverage**: more fiscal years per bank (only FY2024 is cached
  now) and other pilot-bank countries — Germany/Ireland are flagged as
  unconfirmed coverage gaps on `filings.xbrl.org`.
- **Cross-check `entities.csv` against P3DH's own Entity list** once the scraper
  (1.1) is verified — the exercise participant lists are a proxy, not confirmed
  ground truth for who's live on P3DH.
- **Watch ESAP** (the EU's European Single Access Point): if it becomes genuinely
  live and populated, evaluate replacing some per-source acquisition modules with
  it.
- **Archive `add-mvp-v1`** into `openspec/specs/data-retrieval/` once the tasks
  above are resolved.
