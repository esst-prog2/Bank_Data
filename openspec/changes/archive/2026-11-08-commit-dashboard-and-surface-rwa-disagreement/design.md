# Design

No new design decisions beyond what's in `proposal.md` - this change doesn't touch
the package's own interface or require a new technical approach, it corrects a
process gap (the demo's own code wasn't in the repository) and brings the dashboard's
display logic in line with a design the package already has (every figure carries its
own source/provenance, never silently reconciled).

## Why no package-level design work was needed

`get_financial_data()` already returns every row for a concept untouched, each tagged
by its own `source`/`provenance`/`source_reporting_item` - that contract didn't change
and didn't need to. The only new logic is in the dashboard's own precompute script
(`dashboard/build_comparison_data.py`), which previously collapsed multiple rows at the
same provenance tier down to one display value unconditionally. The fix is a detection
step ahead of that same precedence pick, not a replacement for it:

1. Rows are still grouped by provenance tier exactly as before (`reported_actual` >
   `restated_actual` > `scenario_projection`), and the existing source/row-code
   tie-break still decides which single value is shown as the cell's headline number -
   this preserves every other concept/cell's existing display behavior unchanged.
2. Only within the *best* tier, and only when that tier is `reported_actual`
   specifically, do multiple rows get compared against each other for a real
   (> 0.1%, chosen to clear floating-point/export noise seen between EU KM1 and EU
   OV1's otherwise-identical TREA totals for 26 of 28 pilot banks) numeric
   disagreement. `scenario_projection` rows are excluded from this check on purpose:
   EBA's stress test publishes two scenarios (baseline/adverse) under the same item
   code, which legitimately differ - that's not a disagreement about a measured fact,
   it's two different projected futures, and flagging it as a "disagreement" would
   misrepresent what the number is.
3. When a real disagreement is found, every value at that tier is kept (tagged by its
   own source template) alongside the normal single-value pick, rather than replacing
   it - so every existing consumer of a plain `{status, value}` cell (CSV export,
   derived %-of-assets/%-of-RWA/%-of-equity ratios, "best value" highlighting) keeps
   working unchanged, and only the results-table renderer needed a new branch to show
   the extra information when present.

## Alternatives considered

- **Hardcode the Erste Group / total_risk_exposure_amount case specifically.** Rejected
  once checking all 28 banks found a second real instance (~0.3% gap) - a per-bank
  special case would have missed it, and genericizing the check instead is barely more
  code than hardcoding one LEI.
- **Show disagreement for every concept/tier, including scenario projections.**
  Rejected per point 2 above - would have mislabeled EBA's own two stress scenarios as
  a data disagreement, which they're not.
