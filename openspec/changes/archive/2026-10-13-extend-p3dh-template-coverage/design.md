# Design

## Context

`reconcile._p3dh_rows()` already supports two different source-item lookup shapes
behind one `item_code` format (`<template>::<Row|Open Key>=<match value>::<column>`):
a fixed EBA row code (EU KM1) and a per-filer "Open Key" breakdown label (EU LI1), with
a genuinely-absent match surfacing as `missing_from_source` rather than an error (see
`reconcile.py`'s module and `_p3dh_rows()`/`_read_p3dh_fact()` docstrings, 2026-10-12).
`run_update.py` is already idempotent and state-tracked (`data/state/download_log.json`,
keyed by `lei|wave_id|module`) - re-running after an interruption skips everything
already successful, with failures classified by cause (`task 1.4`). `data/modules.txt`
now lists the full 114-template P3DH catalog (configuration only, not yet exercised at
that scale - see proposal.md).

## Goals / Non-Goals

**Goals:**
- Decide, for a short list of concrete candidate templates, whether each is safe to map
  into standardized concepts - grounded in a real cached/scraped export, not the
  template's name alone.
- Wire whichever candidates turn out KM1-shaped (fixed row codes) into `CONCEPT_MAP`,
  reusing the existing `_p3dh_rows()`/`_read_p3dh_fact()` machinery - no new lookup
  mechanism should be needed, since it already generalizes across both shapes found so
  far.
- Plan the real acquisition cost (46 banks x 114 templates) realistically, without
  either attempting it in one sitting or inventing new infrastructure the project
  doesn't need.

**Non-Goals:**
- Wiring every one of the 114 templates - most will likely stay unmapped, either
  because they're too bank-specific (like most of EU LI1) or because they report
  concepts outside this project's current scope (e.g. the climate-risk templates,
  K_41-K_50; the remuneration templates, K_30-series).
- Building new scheduling infrastructure (cron jobs, a job queue, a dashboard).
  `run_update.py`'s existing idempotency plus its `--limit` flag are enough to run a
  multi-day acquisition in however many separate invocations fit the available time,
  each one picking up exactly where the last left off.

## Decisions

**Inspect before wiring, every time - no exceptions for a template that "looks like"
EU KM1 from its name.** EU LI1 looked like it might be KM1-shaped before it was
actually opened; it wasn't. The concrete process for each candidate: fetch (or reuse
an already-cached) export for one or two sample banks, open it directly with openpyxl,
and check whether its `Row` column carries a real, non-null, EBA-style code - if so,
treat it as KM1-shaped; if `Row` is empty and `Open Key` carries the real breakdown
label instead, treat it as LI1-shaped and apply the same scrutiny LI1 got (check at
least one other bank's export before assuming a label generalizes).

**Reuse `_p3dh_rows()`'s existing item-code format rather than adding a third shape.**
Both shapes found so far (fixed row code, per-filer Open Key) are already expressible
in the current `"<template>::<field>=<value>::<column>"` format. Unless a newly
inspected template turns out to need a genuinely different lookup (e.g. matching on a
combination of two fields at once), no change to `_read_p3dh_fact()` itself should be
needed - only new `CONCEPT_MAP` entries.

**Validate a template on a small sample before fetching it for the full pilot.**
Fetching a template across all 46 pilot banks before confirming it's worth wiring
would spend a meaningful slice of the week-long acquisition budget on something that
might turn out unusable. For each candidate, fetch it for only the already-cached
reference dates of 2-3 pilot banks (e.g. Erste, plus one bank already known to have
good EU LI1 coverage and one that didn't) first; only schedule the full 46-bank pass
once the template is confirmed worth it.

**Bank-major loop order, unchanged.** `run_update.py` already loops entity-outer,
module-inner. Keeping that order (rather than flipping to template-major) means a
single run can be stopped after any whole entity and cleanly resumed - re-ordering to
"one template, all banks" would risk leaving an entity's OTHER, already-fetched
templates orphaned mid-record if interrupted. The existing per-(lei, wave_id, module)
state keying doesn't care which order filled it in, so this is a pure scheduling
choice, not a data-model one.

**Batching is `--limit` plus repeated invocation, not new infrastructure.**
`run_update.py`'s existing `--limit` flag (attempt only the first N entities) combined
with its state file already gives exactly the resumability a multi-day run needs.
Running it from several separate background invocations - this session's or a future
one's - each covering a chunk of entities/templates, is sufficient; no new scheduler,
queue, or persistent service is proposed.

## Risks / Trade-offs

- A template looks KM1-shaped from its name or EBA documentation but turns out
  per-filer/LI1-shaped only once a real export is opened → mitigated by this change's
  own core rule: inspect a real export before wiring, every time, now also stated as an
  explicit spec requirement (not just a convention).
- The full 46-bank x 114-template fetch is ~week-scale; run inline it risks silently
  stalling or erroring without anyone noticing → mitigated by `run_update.py`'s existing
  per-entity state persistence and failure-type classification (task 1.4), so a run can
  be interrupted and resumed, and its failure modes read back after the fact, without a
  dedicated monitoring system.
- Fetching a template broadly before confirming its value wastes acquisition budget on
  something unusable → mitigated by the small-sample validation step above.
- EBA could change the Template list or a template's own layout during the time this
  takes → no new mitigation beyond what's already true of this project: a broad,
  sudden rise in `scraper_error`/`template_or_date_not_available` failures (task 1.4's
  classification) is the existing signal something changed upstream, re-scrape the
  Template list (as this change's own investigation just did) if that happens.
