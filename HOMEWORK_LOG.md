# Homework write-ups

Non-code homework submissions (the "what to write" kind, not the "what to build"
kind — those are the commits themselves). One section per homework, append only —
never rewrite an earlier section, same convention as `PLANNING_LOG.md`.

## Homework 7 (2026-10-27)

**1. What moved forward.**

Three things, each a real commit on `main`:

- **Fixed a real test-suite fragility bug.** A code review flagged 4 tests that
  crash with `DataSourceError` instead of skipping cleanly on a fresh clone (no
  cached data). Checking it empirically (not just reading the code) found 7, not
  4. Also replaced two weak tests — one that checked a value computed by running
  the function under test itself, one that only checked an algebraic identity
  true for any input — with real hand-calculated unit tests using invented,
  known-answer data.
  [`b8e97df`](https://github.com/esst-prog2/Bank_Data/commit/b8e97df)

- **Removed the DuPont analysis feature from the shared repo.** Decided it
  wasn't worth the remaining time against the original pitch, kept a backup on
  my own machine (never pushed), and removed it from `reconcile.py` and both
  test files via a new commit rather than rewriting history.
  [`71f66c6`](https://github.com/esst-prog2/Bank_Data/commit/71f66c6)

- **Investigated whether Germany's missing ESEF data could be added, and closed
  it as a documented gap.** Surveyed all 30 EU/EEA national registries (ESMA's
  official OAM list) as potential sources beyond the one aggregator already
  wired, then directly checked Germany's own registry with a real search. The
  filings genuinely exist there and are free to search — but the actual
  documents are gated behind a real, named CAPTCHA, which I decided not to
  attempt to defeat. Decided not to pursue a manual one-off download either, so
  this is now a closed, explained gap rather than an open thread.
  [`e1ad4ed`](https://github.com/esst-prog2/Bank_Data/commit/e1ad4ed),
  [`e7481ca`](https://github.com/esst-prog2/Bank_Data/commit/e7481ca),
  [`1f1b062`](https://github.com/esst-prog2/Bank_Data/commit/1f1b062)

**2. One question.**

Erste Group's EU OV1 and EU KM1 templates each report their own total
risk-weighted exposure amount for the same bank and period, and they don't
match (€149,673.86m vs €147,487.07m — a real ~1.5% gap). My package returns
both, tagged by their own source template, rather than resolving or picking
one — that's the whole point of the provenance design. Is showing an unresolved
disagreement like that, live in the 5-minute demo, the right thing to do, or
does an unexplained discrepancy read as "not finished" to the audience?
