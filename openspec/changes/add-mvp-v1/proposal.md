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
- Every returned value carries source and comparability metadata: which
  XBRL/ESEF or regulatory reporting item produced it, and which standardized
  concept it maps to.
- Values that cannot be established as economically comparable across sources
  are never silently combined; they are reported as non-comparable, with a
  reason where available.
- Values genuinely absent from the source are distinguished from values that
  could not be retrieved or processed (a package/source failure).
- Coverage is intentionally narrow: a defined set of pilot banks and a defined
  set of variables, not comprehensive EU coverage — see the "Not this term"
  list in README.md section 3, which stays out of scope for this change.

## Impact

- Affected specs: `openspec/specs/data-retrieval/` (new capability)
- Affected code: `data_acquisition/*` (entity/period/variable resolution surface
  on top of the existing scraper/downloader modules), plus new reconciliation
  logic (source-item -> standardized-concept mapping, comparability checks)
  called out in AGENTS.md's "Immediate next steps" #6 as the main technical risk.
- Depends on at least one data source being reliably wired up end-to-end first
  (see AGENTS.md steps 1-3: verify the P3DH scraper, populate `data/entities.csv`,
  create `data/modules.txt`) — this proposal defines the target contract, it does
  not assume the sources are already working.
