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

**Addendum (2026-10-29).** Work continued past this write-up's original scope,
so this note exists only so HW7 doesn't read as the final state of the
project. Two more metrics (RWA density, net fee income) were added
2026-10-28, and the two deferred ones (cost-to-income ratio, total revenue)
were built 2026-10-29, closing out the "add next metrics" ask in full.
Separately — and the bigger change — the demo itself moved from the README's
function-call pitch to an interactive map-based dashboard (select a basket of
banks on a map, pick what to compare, see a results table), built out
completely across 2026-10-28/29. See Homework 8 below for the actual
write-up of that work, including an answer to this section's open question.

## Homework 8 (2026-11-01)

**1. What moved forward.**

Two things, each real commits on `main`:

- **Finished the three deferred metrics.** Added `net_fee_income` to
  CONCEPT_MAP, then RWA density, then — after a direct, bank-by-bank survey
  of all 28 pilot banks' cached ESEF facts rather than guessing a formula
  first — `total_revenue` and `compute_cost_to_income_ratio()`. The survey
  found IFRS genuinely doesn't mandate one income-statement shape for banks:
  13/28 filers tag a single already-totaled opex/revenue line, 6/28 (5
  Spanish banks + Erste) instead report 3 granular expense lines summed
  against a `GrossProfit` tag, and Erste alone needed a 3rd fallback built
  from its individually-tagged P&L lines. Along the way, found and fixed two
  real bugs in `compute_rwa_density()` (a non-EUR total_assets case, and a
  P3DH export-scale inconsistency) and a currency-mislabeling bug that had
  silently affected three different concepts — fixed systemically by adding
  a real `currency` column to `get_financial_data()`'s DataFrame instead of
  patching each symptom separately.
  [`a5f19bc`](https://github.com/esst-prog2/Bank_Data/commit/a5f19bc),
  [`8b23d05`](https://github.com/esst-prog2/Bank_Data/commit/8b23d05),
  [`6a58380`](https://github.com/esst-prog2/Bank_Data/commit/6a58380)

- **Rebuilt the demo as an interactive dashboard.** Replaced the README's
  planned function-call walkthrough with a 5-step user journey: a map of
  Europe with real bank logos, hover-for-key-metrics, click-to-build a basket
  of up to 6 banks, a concept/scope picker modal, and a results table
  comparing the selected banks on the selected metrics. The table has no
  live Python backend — every displayed value is precomputed offline by a
  script that calls `get_financial_data()` / `compute_rwa_density()` /
  `compute_cost_to_income_ratio()` exactly as shipped, so the demo can never
  show a number the real package wouldn't. Missing values show a dash with a
  hover reason instead of a bare blank; CSV export and "highlight the best
  value" (restricted to metrics where "better" is unambiguous, e.g. CET1
  ratio but not total assets) were both added per direct user sign-off.
  [`8d24c55`](https://github.com/esst-prog2/Bank_Data/commit/8d24c55)

**2. Answer to last week's question** (the Erste OV1-vs-KM1 TREA mismatch).

The package itself still doesn't resolve it — `get_financial_data()` returns
both rows, each tagged by its own source template, exactly as before; that
part of the design didn't change. But building the results table forced a
real answer to the demo question, because a table cell can't show two
numbers. The fix was to add an explicit, documented precedence rule for
exactly this situation — real reported figures over restated or projected
ones, then ESEF over P3DH over the stress test, and for this specific
concept, EU KM1 preferred over EU OV1 — so the table shows one clean number
by default. That's a display-layer convenience, not a reconciliation: the
underlying DataFrame still carries both figures, so anyone who asks "where
did this number come from" one level down still finds the disagreement
instead of a false consensus.

**3. One question.**

`total_revenue` and `cost_to_income_ratio` are only available for 18/28 and
16/28 pilot banks — real reporting heterogeneity, not a bug, same story as
every other coverage gap in this project. But a user picking a random
6-bank basket for the live demo has a decent chance of landing on a row
that's mostly dashes. Is a sparse row like that a good illustration of the
project's actual point (real data is genuinely incomplete and inconsistent
across banks), or does it just read as "this demo doesn't work" to someone
seeing it for the first time, with no context for why?

**Addendum (2026-11-02).** Two more real commits landed later the same day
this write-up was submitted, so it's noted here rather than silently
missing: the README's section 1 was updated to describe the dashboard
itself as the actual demo (previously it still framed the dashboard as an
addition on top of the original function-call pitch), and two more
metrics — NPL ratio and ROE — were wired into the dashboard. NPL ratio
reuses `compute_npl_ratio()` (already built and tested, just never wired
into the dashboard before); coverage is 26/28 banks, all plausible values.
ROE is a third client-side ratio computed against total equity, deliberately
left out of "best"-value highlighting for the same reason ROA already was —
a higher margin against a smaller equity base isn't unambiguously "better."
Doesn't change either answer above.
