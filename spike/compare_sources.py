"""Spike script for GitHub issue #4 ("Your spike: why do your two sources disagree
on Erste?"). Throwaway, not part of the package.

Pulls reconcile.py's own output for Erste Group Bank AG FY2024 (period 202412) and
prints it next to the same figures as published in Erste's own 2024 Annual Report
and 2024 Pillar 3 Disclosure Report, with the delta for each. Also computes RWA
density (TREA / total assets) two ways, since TREA and total assets never come from
the same source in this project.

Run: python spike/compare_sources.py
Requires data/raw/stress_test/2025/TRA_OTH.csv and the cached ESEF facts for
PQOH26KWDF7CG10L6792/2024-12-31 (see AGENTS.md for how to regenerate both).

The reference figures below are quoted, with page numbers, in spike/comparison.md -
that file is the actual evidence; this script just recomputes the reconcile.py side
so the comparison isn't a one-off manual reading.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_acquisition import reconcile

_BANK_LEI = "PQOH26KWDF7CG10L6792"
_PERIOD = "202412"

# Quoted directly from Erste Group's own published reports (see spike/comparison.md
# for the exact lines, page numbers, and source URLs).
_REFERENCE = {
    # Consolidated statement of income, 1-12 24 column.
    # AR2024_Group_Consolidated_Financial_Statements_en.pdf, p.236 ("Consolidated
    # statement of income"), row "Net interest income".
    "net_interest_income": 7528.0,
    # Same page, row "Net result for the period" (before minority split - the group
    # total, which is what a supervisory template like the stress test's is scoped to).
    "profit_or_loss_for_the_year": 3945.0,
    # 2024_Disclosure_Report.pdf ("Disclosure Report 2024"), p.29, Table 7 "Key
    # metrics template" (EU KM1), column a (31/12/2024), row "Common Equity Tier 1
    # (CET1) capital".
    "cet1_capital": 23995.7,
    # Same table, row "Total risk-weighted exposure amount".
    "total_risk_exposure_amount": 157240.7,
}


def main() -> None:
    df = reconcile.get_financial_data(
        _BANK_LEI,
        ["net_interest_income", "profit_or_loss_for_the_year", "cet1_capital",
         "total_risk_exposure_amount", "total_assets"],
        period=_PERIOD,
    )

    print(f"{'concept':<28} {'source':<16} {'provenance':<18} {'value':>14} {'reference':>14} {'delta':>10} {'delta %':>8}")
    for concept in ["net_interest_income", "profit_or_loss_for_the_year",
                    "cet1_capital", "total_risk_exposure_amount"]:
        ref = _REFERENCE[concept]
        rows = df[df["standardized_concept"] == concept]
        for _, row in rows.iterrows():
            delta = row["value"] - ref
            pct = delta / ref * 100
            print(f"{concept:<28} {row['source']:<16} {row['provenance']:<18} "
                  f"{row['value']:>14,.2f} {ref:>14,.2f} {delta:>10,.2f} {pct:>7.2f}%")

    total_assets = df.loc[df["standardized_concept"] == "total_assets", "value"].iloc[0]
    trea_actual = df.loc[
        (df["standardized_concept"] == "total_risk_exposure_amount")
        & (df["provenance"] == "reported_actual"),
        "value",
    ].iloc[0]
    trea_restated = df.loc[
        (df["standardized_concept"] == "total_risk_exposure_amount")
        & (df["provenance"] == "restated_actual"),
        "value",
    ].iloc[0]

    print()
    print(f"total_assets (esef, reported_actual): {total_assets:,.2f}")
    print(f"RWA density, TREA actual   / total_assets = {trea_actual / total_assets:.4f} "
          f"({trea_actual / total_assets * 100:.1f}%)")
    print(f"RWA density, TREA restated / total_assets = {trea_restated / total_assets:.4f} "
          f"({trea_restated / total_assets * 100:.1f}%)")


if __name__ == "__main__":
    main()
