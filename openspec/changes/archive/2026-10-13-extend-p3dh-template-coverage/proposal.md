# Proposal

## Why

Only 2 of P3DH's 114 real Data Points Report templates (EU KM1, partially EU LI1) are
ever read by `reconcile.py`, so the package's regulatory coverage is limited to capital
adequacy and two balance-sheet totals - nothing on risk-weighted-asset composition,
asset quality, or own-funds structure, each a real gap in what the package can return.
Wiring EU LI1 (2026-10-12) also surfaced a real risk worth addressing now, before more
templates get wired the same ad hoc way: not every template maps cleanly to a
standardized concept the way EU KM1's fixed EBA row codes do - EU LI1's own line items
turned out to be identified by each bank's own "Open Key" vocabulary, not a shared code,
and a template that looks KM1-shaped from its name alone could turn out the same way.
The project needs a documented rule for which templates are safe to map, applied to a
short list of concrete next candidates, before committing to wiring any of them -
and a realistic plan for actually acquiring the data, since a live run across the full
46-bank pilot sample and the now-114-template catalog is on the order of a week of
continuous scraping, not a quick follow-up fetch.

## What Changes

- `data/modules.txt` already expanded (2026-10-12, ahead of this proposal) from 2
  templates to the full real P3DH catalog of 114 templates, scraped directly from the
  live Template slicer rather than estimated - this is configuration only; `run_update.py`
  has not yet been run against the expanded list.
- Add an explicit, product-observable rule (not just a code comment) for when a source
  item is safe to map into a standardized concept at all: only when the source's own
  structure identifies that item unambiguously and the same way for every bank (a fixed
  row/item code), never by inferring a mapping from a per-filer breakdown label. A
  per-filer label absent from a given bank's own export must surface as
  missing-from-source for that one fact, never be guessed at or silently skipped.
- Inspect a short list of promising next templates against real cached exports (not
  guessed from their names) before committing to wiring any of them: EU OV1 (RWA by
  risk type), the EU CQ-series (credit quality / non-performing exposures), and EU CC1
  (composition of regulatory own funds) are the current candidates.
- For each inspected template, decide and document whether it's wired into
  `CONCEPT_MAP` (clean, fixed-row shape, like EU KM1) or explicitly excluded (per-filer
  or otherwise too ambiguous to map safely, like most of EU LI1) - no template is left
  silently unevaluated.
- Plan a scheduled, batched acquisition pass across the full pilot sample and expanded
  template list, sized to its real ~week-long scale rather than attempted in one sitting.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `data-retrieval`: add a requirement stating the concept-mapping safety rule above -
  this generalizes a rule the EU LI1 work already followed in practice (reconcile.py's
  module docstring, 2026-10-12) into an explicit, testable part of the package's
  contract, so it governs every future template the same way, not just LI1's.

## Impact

- `data_acquisition/reconcile.py`: new `CONCEPT_MAP` entries for whichever inspected
  templates turn out to be safely mappable; no change for ones excluded, beyond a
  documented reason.
- `data_acquisition/run_update.py`: may need batching/resumability support suited to a
  multi-day run across 46 banks x 114 templates, beyond its current single-process loop.
- `data/modules.txt`: already changed (see above); no further change expected unless a
  template turns out not worth fetching at all (e.g. genuinely empty across the pilot
  sample) and is deliberately removed.
- `tests/test_reconcile.py`: new tests for each newly-wired concept, following the
  existing pattern (real cached data, cross-checked against an independent source where
  one exists).
- `DATA_SOURCES_NOTES.md` / `PLANNING_LOG.md`: a dated entry per inspected template,
  regardless of whether it ends up wired.
