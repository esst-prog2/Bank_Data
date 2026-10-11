"""Tests for data_acquisition.reconcile against the real, downloaded EBA Stress Test
2025 data (data/raw/stress_test/2025/TRA_OTH.csv). Requires that file to exist - run
`python -m data_acquisition.eba_exercises stress_test 2025` first.

Covers tasks.md section 4's acceptance criteria and the corresponding scenarios in
openspec/changes/add-mvp-v1/specs/data-retrieval/spec.md.
"""

from __future__ import annotations

import pandas as pd
import pytest

from data_acquisition import reconcile

# Erste Group Bank AG (Austria) - a real participant in the EBA Stress Test 2025.
_BANK_LEI = "PQOH26KWDF7CG10L6792"


@pytest.fixture(scope="module")
def _source_available():
    if not reconcile._STRESS_TEST_OTH_CSV.exists():
        pytest.skip(
            "data/raw/stress_test/2025/TRA_OTH.csv not downloaded - run "
            "`python -m data_acquisition.eba_exercises stress_test 2025` first."
        )


def test_supported_bank_period_and_variable_returns_value_and_mapping(_source_available):
    """4.1 / spec: supported bank + period + available variable -> value, source
    reporting item, and standardized-concept mapping.

    EBA restates some actuals later under the same period (Scenario 11), so this
    period/item genuinely has two rows - itself an instance of the package's "don't
    combine, tag distinctly" principle rather than a single clean value."""
    df = reconcile.get_financial_data(_BANK_LEI, ["cet1_ratio"], period="202412")

    assert set(df["provenance"]) == {"reported_actual", "restated_actual"}
    row = df[df["provenance"] == "reported_actual"].iloc[0]
    assert row["status"] == "ok"
    assert row["standardized_concept"] == "cet1_ratio"
    assert row["source_reporting_item"] == "2531008"
    assert pd.notna(row["value"])
    assert _BANK_LEI in row["origin_reference"]


def test_variable_absent_for_period_is_missing_not_failed(_source_available):
    """4.2 / spec: a variable genuinely absent from the source for that bank/period
    is identified as missing-from-source, not as a retrieval/processing failure."""
    # No bank reports stress-test scenarios for this period - it predates the
    # exercise's projection horizon entirely.
    df = reconcile.get_financial_data(_BANK_LEI, ["cet1_ratio"], period="209912")

    assert len(df) == 1
    row = df.iloc[0]
    assert row["status"] == "missing_from_source"
    assert row["value"] is None
    assert row["provenance"] is None


def test_reported_actual_and_scenario_projection_both_returned_untagged_as_one(_source_available):
    """4.3 / spec: a reported actual and a stress-test scenario projection for the
    same bank/concept are each tagged with their own provenance, never combined."""
    df = reconcile.get_financial_data(_BANK_LEI, ["cet1_ratio"])  # all periods

    provenances = set(df["provenance"].dropna())
    assert "reported_actual" in provenances
    assert "scenario_projection" in provenances
    # Each row stays a distinct value, not merged into one authoritative figure.
    assert df["standardized_concept"].eq("cet1_ratio").all()
    assert len(df) == df.drop_duplicates(subset=["period", "provenance", "value"]).shape[0]


def test_unsupported_variable_is_reported_clearly(_source_available):
    """spec: an unsupported variable is reported clearly, not returned as an empty
    or misleading result."""
    with pytest.raises(reconcile.UnsupportedVariableError):
        reconcile.get_financial_data(_BANK_LEI, ["quantum_flux_capacitor_ratio"])


def test_unsupported_bank_is_reported_clearly(_source_available):
    """spec: an unsupported bank is reported clearly, not returned as an empty or
    misleading result."""
    with pytest.raises(reconcile.UnsupportedBankError):
        reconcile.get_financial_data("NOTALEIXXXXXXXXXXXXX", ["cet1_ratio"])


def test_retrieval_failure_is_raised_not_returned_as_missing(tmp_path):
    """spec: a genuine retrieval/processing failure raises explicitly rather than
    being reported as missing-from-source."""
    missing_file = tmp_path / "does_not_exist.csv"
    with pytest.raises(reconcile.DataSourceError):
        reconcile.get_financial_data(
            _BANK_LEI, ["cet1_ratio"], csv_path=missing_file,
        )


@pytest.fixture(scope="module")
def _esef_available():
    from data_acquisition import esef_client
    cache = reconcile._ROOT / "data" / "raw" / "esef" / _BANK_LEI / reconcile._ESEF_PERIOD_END / "facts.json"
    if not cache.exists():
        pytest.skip(
            "ESEF facts not cached - run esef_client.fetch_facts() for "
            f"{_BANK_LEI}/{reconcile._ESEF_PERIOD_END} first (needs network access)."
        )


def test_two_independent_sources_report_same_concept_untagged_as_one(_source_available, _esef_available):
    """4.3 / spec, the stronger case: net interest income comes from two
    INDEPENDENT reported-actual sources (the stress test's supervisory scope and
    ESEF's IFRS consolidated scope) for the same bank and fiscal year - not one
    actual and one projection from a single source. They're close but not
    identical, and neither is combined into a single authoritative figure."""
    df = reconcile.get_financial_data(_BANK_LEI, ["net_interest_income"], period="202412")

    sources = set(df["source"])
    assert sources == {"eba_stress_test", "esef"}
    assert (df["provenance"] == "reported_actual").all()
    values = df.set_index("source")["value"]
    assert values["eba_stress_test"] != values["esef"]
    # both plausible for the same real bank/year, neither fabricated to agree.
    # 2% relative tolerance, not an arbitrary absolute one: spike/comparison.md
    # traces this gap to Erste's own documented prudential-vs-IFRS scope-of-
    # consolidation difference (Pillar 3 report pp.26-27), which is a structural
    # small-single-digit-percent effect - the observed gap is 0.17%.
    relative_gap = abs(values["eba_stress_test"] - values["esef"]) / values["esef"]
    assert relative_gap < 0.02


def test_esef_only_concept_has_no_stress_test_row(_esef_available):
    """total_assets has no regulatory-capital equivalent in the stress test's
    TRA_SUM template - it should come back from ESEF alone, not padded with an
    unrelated missing-from-source row from a source that was never asked."""
    df = reconcile.get_financial_data(_BANK_LEI, ["total_assets"], period="202412")

    assert len(df) == 1
    row = df.iloc[0]
    assert row["source"] == "esef"
    assert row["status"] == "ok"
    assert row["value"] > 0


@pytest.fixture(scope="module")
def _p3dh_available():
    if not reconcile._cached_p3dh_files("Erste Group Bank AG", "K_61.00"):
        pytest.skip(
            "no cached P3DH EU KM1 export for Erste Group Bank AG - run "
            "data_acquisition.run_update (or the scraper directly) first."
        )


def test_p3dh_concept_returns_one_row_per_cached_reference_date(_p3dh_available):
    """2026-10-11: P3DH wiring (EU KM1 only). get_financial_data(period=None) should
    return one p3dh row per cached reference date for this bank/template - cache-only,
    never a live P3DH query (see reconcile._p3dh_rows's docstring)."""
    df = reconcile.get_financial_data(_BANK_LEI, ["cet1_ratio"], period=None)
    p3dh = df[df["source"] == "p3dh"]

    assert len(p3dh) == len(reconcile._cached_p3dh_files("Erste Group Bank AG", "K_61.00"))
    assert (p3dh["provenance"] == "reported_actual").all()
    assert (p3dh["status"] == "ok").all()
    # decimal fraction, same convention as stress_test's own cet1_ratio - not a percentage.
    assert p3dh["value"].between(0, 1).all()


def test_p3dh_and_stress_test_both_returned_untagged_as_one(_source_available, _p3dh_available):
    """4.3 / spec, the P3DH instance of the same rule the ESEF test above covers.
    P3DH's own cached reference dates (2025-06 onward, launched Jan 2026) don't overlap
    the stress test's single reported_actual period (202412) - so at a period both
    sources actually cover (202512), the stress test only has its own forward-looking
    scenario projections, not a reported actual. Even so, neither source's figure is
    combined with the other's - P3DH's real disclosure stays its own row, untagged as
    one with the stress test's projections."""
    df = reconcile.get_financial_data(_BANK_LEI, ["cet1_ratio"], period="202512")

    sources = set(df["source"])
    assert sources == {"eba_stress_test", "p3dh"}
    p3dh_rows = df[df["source"] == "p3dh"]
    assert len(p3dh_rows) == 1
    assert p3dh_rows.iloc[0]["provenance"] == "reported_actual"
    assert set(df[df["source"] == "eba_stress_test"]["provenance"]) == {"scenario_projection"}


def test_p3dh_returns_no_rows_when_nothing_cached_for_bank():
    """A bank run_update.py hasn't scraped P3DH for yet should return nothing for a
    p3dh-sourced concept - not a fabricated missing_from_source row, since this module
    never live-queries P3DH to confirm the value is actually absent there (see
    reconcile._p3dh_rows's docstring on the cache-only asymmetry)."""
    # HSBC Continental Europe - a real tracked LEI with no cached P3DH export as of
    # 2026-10-11; skip (rather than assert a now-stale fact) if that's since changed.
    lei = "F0HUI1NY1AZMJMD8LP67"
    if reconcile._cached_p3dh_files(reconcile._p3dh_entity_name(lei), "K_61.00"):
        pytest.skip("HSBC Continental Europe now has a cached P3DH export - case no longer applies")
    df = reconcile.get_financial_data(lei, ["cet1_ratio"], period=None)
    assert (df["source"] != "p3dh").all()


def test_rwa_density_uses_reported_actual_trea(_source_available, _esef_available):
    """Homework 5, 2026-10-08. Finished sentence (PLANNING_LOG.md, decided by user): "A
    test would go red if the RWA density calculation ever used restated TREA instead of
    reported_actual TREA as the numerator."

    Expected value, fixed in PLANNING_LOG.md BEFORE this test was written, not derived
    by running this code: RWA density for Erste Group Bank AG FY2024 = 44.5% (precisely
    157,240.73 / 353,736.00 = 0.444514...), from spike/comparison.md's own hand
    calculation - TREA actual EUR 157,240.73m is Erste's own Pillar 3 Disclosure Report
    2024, p.29, Table 7; total assets EUR 353,736.00m is Erste's FY2024 ESEF filing
    (ifrs-full:Assets). Using restated TREA instead (150,251.17) would give ~42.5% - the
    spike's own example of a "plausible-looking but methodologically mismatched number".
    """
    density = reconcile.compute_rwa_density(_BANK_LEI, period="202412")
    assert density == pytest.approx(0.4445, abs=0.0005)


def test_compute_total_revenue_sums_esef_components(_esef_available):
    """2026-10-08, DuPont analysis. Erste's FY2024 filing tags all three Total
    Revenue components directly (net interest income, net fee and commission income,
    and - unlike most banks - the IFRS standard TradingIncomeExpense tag), so this is
    the one bank/period where `complete` should be True and the components sum
    exactly to the reported total: 7,528 + 2,938 + 519 = 10,985 (EUR million, 2024-12-31
    duration facts - 7,528 is the same FY2024 net interest income figure already
    established throughout this project since the spike, e.g.
    spike/comparison.md's own citation to Erste's Annual Report p.236)."""
    revenue = reconcile.compute_total_revenue(_BANK_LEI, "202412")
    assert revenue["complete"] is True
    assert revenue["value"] == pytest.approx(10985.0, abs=1.0)
    assert revenue["components"]["net_interest_income"] == pytest.approx(7528.0, abs=1.0)
    assert revenue["components"]["net_fee_and_commission_income"] == pytest.approx(2938.0, abs=1.0)
    assert revenue["components"]["trading_income"] == pytest.approx(519.0, abs=1.0)


def test_compute_total_revenue_derives_net_fee_from_gross_when_untagged():
    """Most ESEF filers (confirmed 2026-10-08: 28/29 cached banks) tag fee and
    commission income/expense as a gross pair, not a single net fact - Banco
    Santander is one of them (no ifrs-full:FeeAndCommissionIncomeExpense tag).
    compute_total_revenue() must fall back to Income - Expense in that case, not
    report the component as missing. Santander FY2024: income 17,602.0m - expense
    4,592.0m = 13,010.0m (confirmed by direct inspection of the cached filing)."""
    revenue = reconcile.compute_total_revenue("5493006QMFDDMYWIAM13", "202412")
    assert revenue["components"]["net_fee_and_commission_income"] == pytest.approx(13010.0, abs=1.0)


def test_compute_dupont_roe_equals_net_income_over_equity():
    """Structural identity, not an externally-sourced value: however Profit Margin x
    Asset Utilization x Equity Multiplier is computed, it must algebraically reduce to
    Net Income / Total Equity - a regression guard against the three factors drifting
    out of sync with each other (e.g. a future edit using total_assets in one factor
    and average_total_assets in another would break this silently otherwise)."""
    result = reconcile.compute_dupont(_BANK_LEI, "202412")
    assert result.roe == pytest.approx(result.net_income / result.total_equity, rel=1e-9)
    assert result.roe == pytest.approx(
        result.profit_margin * result.asset_utilization * result.equity_multiplier, rel=1e-9
    )


def test_compute_dupont_missing_concept_raises_dupont_error():
    """BNP Paribas reports gross interest income/expense separately, never a single
    net_interest_income total (same finding as the spike's NII investigation) - this
    is correctly a retrieval gap (DuPontError), never a silently fabricated 0."""
    with pytest.raises(reconcile.DuPontError):
        reconcile.compute_dupont("R0MUWSFPU8MPRO8K5P83", "202412")
