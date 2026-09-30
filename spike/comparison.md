# Spike: why do the two sources disagree on Erste?

Answers GitHub issue [#4](https://github.com/esst-prog2/Bank_Data/issues/4). Question
and answer criteria are quoted from the issue, not restated here.

Bank: Erste Group Bank AG (LEI `PQOH26KWDF7CG10L6792`). Period: FY2024 (31 Dec 2024).
Reproduce the `reconcile.py` column with `python spike/compare_sources.py` (needs
`data/raw/stress_test/2025/TRA_OTH.csv` and the cached ESEF facts — see AGENTS.md).

## Sources compared

- **Annual report**: Erste Group, *Group Consolidated Financial Statements 2024
  (IFRS)*, downloaded 2026-09-30 from
  <https://cdn.erstegroup.com/content/dam/at/eh/www_erstegroup_com/en/Investor_Relations/onlinear2024/ar24reports/AR2024_Group_Consolidated_Financial_Statements_en.pdf>.
- **Pillar 3 report**: Erste Group, *Disclosure Report 2024* (pursuant to Part Eight
  CRR), downloaded 2026-09-30 from
  <https://cdn.erstegroup.com/content/dam/at/eh/www_erstegroup_com/en/Investor_Relations/Reg_Disclosure/2024_Disclosure_Report.pdf>.
- **EBA methodology**: EBA, *2025 EU-wide stress test — Methodological Note*, 20 Jan
  2025, <https://www.eba.europa.eu/sites/default/files/2025-01/0246e2f3-fa57-47d1-99f2-7a5b80cae509/2025%20EU-wide%20stress%20test%20-%20Methodological%20Note.pdf>.

## The four deltas

| concept | eba_stress_test (actual) | reference | delta | delta % | cause |
|---|---:|---:|---:|---:|---|
| net interest income | 7,540.51 | 7,528.00 (annual report, p.236, "Net interest income", 1-12 24) | +12.51 | +0.17% | scope of consolidation (see below) |
| profit or loss for the year | 3,913.58 | 3,945.00 (annual report, p.236, "Net result for the period", 1-12 24) | -31.42 | -0.80% | scope of consolidation (see below) |
| CET1 capital | 24,131.77 (restated) vs 23,995.67 (actual) | 23,995.7 (Pillar 3 report, p.29, Table 7 "Key metrics template", col a = 31/12/2024) | actual matches (-0.03); restated +136.07 | actual: -0.00%; restated: +0.57% | CRR3 restatement (see below) |
| total risk exposure amount (TREA) | 150,251.17 (restated) vs 157,240.73 (actual) | 157,240.7 (Pillar 3 report, p.29, same table, "Total risk-weighted exposure amount") | actual matches (+0.03); restated -6,989.53 | actual: +0.00%; restated: -4.45% | CRR3 restatement (see below) |

Quoted lines behind the "reference" column:

> Consolidated statement of income, `AR2024_Group_Consolidated_Financial_Statements_en.pdf`,
> p.236: "Net interest income ... 1-12 24 ... 7,528" ; "Net result for the period ...
> 1-12 24 ... 3,945".

> Table 7: Key metrics template (Art. 447 (a) to (g) and 438 (b) CRR Table EU KM1
> (EU) 2021/637), `2024_Disclosure_Report.pdf`, p.29, column a (31/12/2024): "Common
> Equity Tier 1 (CET1) capital ... 23,995.7" ; "Total risk-weighted exposure amount
> ... 157,240.7".

These two reference figures are also exactly what `esef_client.py` already pulls
from `filings.xbrl.org` for `ifrs-full:InterestRevenueExpense` (7,528.0) and
`ifrs-full:ProfitLoss` (3,945.0) — the ESEF source and the human-readable annual
report PDF agree to the last decimal, which is the expected result since ESEF *is*
the machine-readable form of that same report.

### Cause 1 — net interest income and profit or loss: scope of consolidation

The stress test's `eba_stress_test` figures come from supervisory (FINREP) reporting
on the **prudential scope of consolidation**; the annual report / ESEF figures are on
the **IFRS accounting scope of consolidation**. Erste's own Pillar 3 report documents
that these scopes are not identical: Table 5/6 of `2024_Disclosure_Report.pdf`
(pp.26-27, "Differences between accounting and regulatory scope of consolidation")
shows total assets of 353,736.0 under the published financial statements against
353,708.1 under the regulatory scope of consolidation — a 27.9m gap from consolidating
a slightly different set of entities (e.g. insurance/leasing subsidiaries treated
differently under CRR than under IFRS). The net interest income and profit deltas
found here (12.5m, 31.4m) are the income-statement-side consequence of that same
documented scope difference, not a data error in either source.

### Cause 2 — CET1 capital and TREA: CRR3 restatement, not a data correction

Erste's own Pillar 3 "Key metrics" table matches the stress test's **actual**
(scenario 1) figures for both CET1 capital and TREA almost exactly (to within
0.03m — rounding). It does **not** match the **restated** (scenario 11) figures at
all: those differ by 136.1m (CET1 capital) and 6,989.5m (TREA, 4.45%).

The EBA's 2025 EU-wide stress test methodological note explains why: banks were
required to submit two versions of their 31 Dec 2024 starting point — "actual"
figures as originally reported under the rules in force at that date (CRR2), and
"restated" figures recast under CRR3/CRD VI, which entered into application on
1 January 2025, i.e. after the reference date. Erste's Pillar 3 report for FY2024
was itself prepared and published under CRR2 (the rules in force at 31 Dec 2024),
so it reconciles to the stress test's "actual" scenario, not its "restated" one.
"Restated" is a forward-looking regulatory recast for the stress test's own 3-year
projection horizon, not a correction of the actual — so the earlier assumption in
`design.md` that provenance tagging alone (reported_actual vs restated_actual) fully
captures "how it differs" was incomplete; it captures *that* two values exist, not
*why*, which is what this spike adds.

## RWA density: which numerator?

`total_risk_exposure_amount` only exists in `eba_stress_test`; `total_assets` only
exists in `esef`. The two live on different scopes of consolidation (prudential vs
IFRS accounting, Cause 1 above) and, for TREA specifically, potentially different
capital regimes (CRR2 actual vs CRR3 restated, Cause 2 above) — pairing them into one
ratio is exactly the kind of cross-source reconciliation README.md section 3 says
this package does not do internally. This spike computes it once, by hand, with the
choice justified rather than left implicit:

```
RWA density = TREA (eba_stress_test, reported_actual) / total_assets (esef, reported_actual)
            = 157,240.73 / 353,736.00
            = 44.5%
```

**Numerator: TREA *actual* (157,240.73), not *restated* (150,251.17).** Two reasons:
first, provenance — "restated" is a CRR3 pro-forma recast (Cause 2), and pairing a
post-2025-rules numerator with a denominator (total assets) that was never recast for
CRR3 would silently mix two different rule regimes in one ratio, which is worse than
not computing it at all. Second, external validation — the actual figure is the one
that reconciles to Erste's own published Pillar 3 disclosure (p.29), so it is
independently checkable against a source the bank itself stands behind; the restated
figure only exists inside the EBA stress test template. Using restated TREA instead
gives 42.5% — a plausible-looking but methodologically mismatched number, which is
exactly the failure mode this project exists to prevent.

## What this changes

`tests/test_reconcile.py`'s `test_two_independent_sources_report_same_concept_untagged_as_one`
asserted `abs(values["eba_stress_test"] - values["esef"]) < 100` (EUR million) with no
stated reason. Replaced with a relative-tolerance assertion (2%) with a comment
pointing at this file, since the real, sourced cause (scope-of-consolidation gaps of
0.17%/0.80%) is structurally a small-single-digit-percent effect, not an
arbitrary absolute cutoff.
