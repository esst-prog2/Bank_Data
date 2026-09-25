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
    # both plausible for the same real bank/year, neither fabricated to agree
    assert abs(values["eba_stress_test"] - values["esef"]) < 100


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
