"""Package surface: given a bank + reporting period(s) + requested concepts, return
a reconciled pandas DataFrame of standardized financial/regulatory figures, each
tagged with enough source/provenance metadata to check it against the original
publication (see openspec/changes/add-mvp-v1/specs/data-retrieval/spec.md).

Two real, verified sources are wired in:

- EBA EU-wide Stress Test 2025 bulk CSV (eba_exercises.py, exercise="stress_test").
  Its TRA_SUM template (inside TRA_OTH.csv) reports a mix of P&L and
  regulatory-capital concepts under several "Scenario" codes - confirmed via that
  download's own Metadata_TR.xlsx ("Scenario" sheet): 1 = Actual figures (the
  pre-stress-test starting point, a reported actual), 2 = Baseline projection,
  3 = Adverse projection (both scenario-projected), 11 = Restated.
- ESEF financial statements via filings.xbrl.org (esef_client.py) - one bank's own
  filing for one fiscal year, IFRS-taxonomy-tagged balance-sheet and
  income-statement concepts, all `reported_actual`.

Two of the standardized concepts (net_interest_income,
profit_or_loss_for_the_year) are reported by BOTH sources for the same bank and
period - each source's own figure is returned as its own row, never combined
into one value (spec's "Multiple sources report the same concept" scenario).
The other concepts are source-specific: cet1_ratio/cet1_capital/
total_risk_exposure_amount only come from the stress test (they're regulatory
capital concepts with no IFRS balance-sheet equivalent); total_assets/
total_equity only come from ESEF (no equivalent line in the stress test's
TRA_SUM template).

P3DH is not wired into this module yet - see AGENTS.md "Immediate next steps".
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_acquisition import esef_client
from data_acquisition.entities import load_entities

_ROOT = Path(__file__).resolve().parent.parent
_STRESS_TEST_OTH_CSV = _ROOT / "data" / "raw" / "stress_test" / "2025" / "TRA_OTH.csv"

# EBA Stress Test 2025 "Scenario" codes -> this package's provenance vocabulary.
# Scenario 0 ("no breakdown by scenario") has no single provenance and is excluded;
# items reported only under it are simply not returned by this module.
_SCENARIO_PROVENANCE: dict[int, str] = {
    1: "reported_actual",
    2: "scenario_projection",  # baseline
    3: "scenario_projection",  # adverse
    11: "restated_actual",
}

# Static per-item lookup table (design.md decision 1): (source, source_item_code) ->
# standardized_concept. Stress-test items sourced from
# data/raw/stress_test/2025/Data_Dictionary.xlsx (sheet "SDD", template TRA_SUM).
# ESEF items are IFRS taxonomy concept names, confirmed present (as undimensioned
# totals) in Erste Group's FY2024 filing via esef_client.
CONCEPT_MAP: dict[tuple[str, str], str] = {
    ("stress_test", "2531001"): "net_interest_income",
    ("stress_test", "2531004"): "profit_or_loss_for_the_year",
    ("stress_test", "2531006"): "cet1_capital",
    ("stress_test", "2531007"): "total_risk_exposure_amount",
    ("stress_test", "2531008"): "cet1_ratio",
    ("esef", "ifrs-full:Assets"): "total_assets",
    ("esef", "ifrs-full:Equity"): "total_equity",
    ("esef", "ifrs-full:InterestRevenueExpense"): "net_interest_income",
    ("esef", "ifrs-full:ProfitLoss"): "profit_or_loss_for_the_year",
}

# Whether an ESEF concept is a balance-sheet instant (as-of a date) or an
# income-statement duration (over the fiscal year) - decides which XBRL period
# key to look it up under.
_ESEF_PERIOD_KIND: dict[str, str] = {
    "ifrs-full:Assets": "instant",
    "ifrs-full:Equity": "instant",
    "ifrs-full:InterestRevenueExpense": "duration",
    "ifrs-full:ProfitLoss": "duration",
}

# This module only has one ESEF filing cached (Erste Group's FY2024) - see
# esef_client's module docstring on why that's a deliberate scope limit, not an
# oversight. A period request outside this simply gets no ESEF rows, never a
# fabricated "missing" for a year nobody asked this module to fetch.
_ESEF_PERIOD_END = "2024-12-31"
_ESEF_PERIOD = "202412"

_ITEMS_BY_CONCEPT: dict[str, list[tuple[str, str]]] = {}
for (_source, _item), _concept in CONCEPT_MAP.items():
    _ITEMS_BY_CONCEPT.setdefault(_concept, []).append((_source, _item))

SUPPORTED_CONCEPTS = frozenset(_ITEMS_BY_CONCEPT)

_DATAFRAME_COLUMNS = [
    "bank_lei", "period", "standardized_concept", "source_reporting_item",
    "source", "provenance", "value", "status", "origin_reference",
]


class UnsupportedBankError(ValueError):
    """Requested bank is outside this module's defined v1 coverage (data/entities.csv)."""


class UnsupportedVariableError(ValueError):
    """Requested concept is outside this module's defined v1 coverage."""


class DataSourceError(RuntimeError):
    """The underlying source data could not be read or parsed - a genuine
    retrieval/processing failure, never conflated with a value that is simply
    absent from the source (spec's "Retrieval or processing failure" scenario)."""


def _load_stress_test_oth(csv_path: Path = _STRESS_TEST_OTH_CSV) -> pd.DataFrame:
    if not csv_path.exists():
        raise DataSourceError(
            f"{csv_path} not found - run "
            "`python -m data_acquisition.eba_exercises stress_test 2025` first."
        )
    try:
        return pd.read_csv(csv_path, dtype={"Item": str, "Period": str})
    except (pd.errors.ParserError, OSError, UnicodeDecodeError) as exc:
        raise DataSourceError(f"failed to read {csv_path}: {exc}") from exc


def _known_bank_leis() -> set[str]:
    return {e.lei for e in load_entities()}


def _stress_test_rows(df: pd.DataFrame, bank_lei: str, bank_name: str, concept: str, item_code: str, period: str | None) -> list[dict]:
    match = df[(df["LEI_Code"] == bank_lei) & (df["Item"] == item_code)]
    if period is not None:
        match = match[match["Period"] == period]
    match = match[match["Scenario"].isin(_SCENARIO_PROVENANCE)]

    if match.empty:
        return [{
            "bank_lei": bank_lei, "period": period, "standardized_concept": concept,
            "source_reporting_item": item_code, "source": "eba_stress_test",
            "provenance": None, "value": None, "status": "missing_from_source",
            "origin_reference": f"EBA EU-wide Stress Test 2025, item {item_code}",
        }]

    rows = []
    for _, r in match.iterrows():
        scenario = int(r["Scenario"])
        rows.append({
            "bank_lei": bank_lei, "period": r["Period"], "standardized_concept": concept,
            "source_reporting_item": item_code, "source": "eba_stress_test",
            "provenance": _SCENARIO_PROVENANCE[scenario], "value": r["Amount"], "status": "ok",
            "origin_reference": (
                f"EBA EU-wide Stress Test 2025, {bank_name} ({bank_lei}), "
                f"item {item_code}, scenario {scenario}"
            ),
        })
    return rows


def _esef_rows(bank_lei: str, concept: str, item_code: str, period: str | None) -> list[dict]:
    if period is not None and period != _ESEF_PERIOD:
        return []  # this module has no filing cached for that period - see docstring

    try:
        facts = esef_client.fetch_facts(bank_lei, _ESEF_PERIOD_END)
    except esef_client.EsefNotFoundError:
        return [{
            "bank_lei": bank_lei, "period": _ESEF_PERIOD, "standardized_concept": concept,
            "source_reporting_item": item_code, "source": "esef",
            "provenance": None, "value": None, "status": "missing_from_source",
            "origin_reference": f"ESEF (filings.xbrl.org), {bank_lei}, no filing for {_ESEF_PERIOD_END}",
        }]
    except esef_client.EsefDataError as exc:
        raise DataSourceError(str(exc)) from exc

    duration_key, instant_key = esef_client.fiscal_year_keys(_ESEF_PERIOD_END)
    period_key = instant_key if _ESEF_PERIOD_KIND[item_code] == "instant" else duration_key
    value = esef_client.get_concept_value(facts, item_code, period_key)
    filing = esef_client.find_filing(bank_lei, _ESEF_PERIOD_END)

    if value is None:
        return [{
            "bank_lei": bank_lei, "period": _ESEF_PERIOD, "standardized_concept": concept,
            "source_reporting_item": item_code, "source": "esef",
            "provenance": None, "value": None, "status": "missing_from_source",
            "origin_reference": f"ESEF filing {filing.report_url}, concept {item_code} not tagged as a total",
        }]

    return [{
        "bank_lei": bank_lei, "period": _ESEF_PERIOD, "standardized_concept": concept,
        "source_reporting_item": item_code, "source": "esef",
        "provenance": "reported_actual", "value": value / 1_000_000, "status": "ok",
        "origin_reference": f"ESEF filing (FY2024), {filing.report_url}, concept {item_code}",
    }]


def get_financial_data(
    bank_lei: str,
    concepts: list[str],
    period: str | None = None,
    csv_path: Path = _STRESS_TEST_OTH_CSV,
) -> pd.DataFrame:
    """Return a DataFrame with one row per (period, standardized_concept, source)
    combination for `bank_lei` (design.md decision 3).

    `period` narrows to one EBA reporting period (e.g. "202412"); leave it None to
    return every period this module's wired sources report for the requested
    concepts - the only way to see a reported actual, its restatement, and a
    scenario-projected figure side by side, since they land in different periods.

    Raises UnsupportedVariableError / UnsupportedBankError for a concept or bank
    outside this module's defined v1 coverage, and DataSourceError if a wired
    source can't be read - never silently as a missing value.
    """
    unsupported = [c for c in concepts if c not in SUPPORTED_CONCEPTS]
    if unsupported:
        raise UnsupportedVariableError(
            f"not in v1 coverage: {unsupported} (supported: {sorted(SUPPORTED_CONCEPTS)})"
        )
    if bank_lei not in _known_bank_leis():
        raise UnsupportedBankError(f"{bank_lei} is not a tracked v1 pilot bank")

    needs_stress_test = any(src == "stress_test" for c in concepts for src, _ in _ITEMS_BY_CONCEPT[c])
    df = _load_stress_test_oth(csv_path) if needs_stress_test else None
    bank_name = bank_lei
    if df is not None:
        names = df.loc[df["LEI_Code"] == bank_lei, "Bank_name"]
        if not names.empty:
            bank_name = names.iloc[0]

    rows: list[dict] = []
    for concept in concepts:
        for source, item_code in _ITEMS_BY_CONCEPT[concept]:
            if source == "stress_test":
                rows.extend(_stress_test_rows(df, bank_lei, bank_name, concept, item_code, period))
            elif source == "esef":
                rows.extend(_esef_rows(bank_lei, concept, item_code, period))
    return pd.DataFrame(rows, columns=_DATAFRAME_COLUMNS)
