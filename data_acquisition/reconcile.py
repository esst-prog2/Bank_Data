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

from dataclasses import dataclass
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
    # Added 2026-10-08 for compute_total_revenue()/compute_dupont() (homework: DuPont
    # analysis). FeeAndCommissionIncomeExpense is the NET concept some filers tag
    # directly (e.g. Erste); most only tag the gross Income/Expense pair (confirmed:
    # 28/29 cached FY2024 banks have the gross pair, only 16/29 tag net directly) -
    # compute_total_revenue() prefers the net tag and falls back to Income - Expense.
    # TradingIncomeExpense is the IFRS *standard* taxonomy concept for trading
    # income, but only 9/29 cached banks actually use it - most tag it under their
    # own custom extension taxonomy (e.g. bnpp:NetGainOnFinancialInstruments...,
    # san:GainsLossesOnFinancialAssetsAndLiabilitiesHeldForTrading), which this
    # static per-item table deliberately does not attempt to chase per-bank (see
    # design.md decision 1 - a static table trades comprehensiveness for
    # reviewability; mapping ~20 banks' individual extension concepts would be
    # exactly the curation-cost blowup that decision accepted as a non-goal for v1).
    ("esef", "ifrs-full:FeeAndCommissionIncome"): "fee_and_commission_income",
    ("esef", "ifrs-full:FeeAndCommissionExpense"): "fee_and_commission_expense",
    ("esef", "ifrs-full:FeeAndCommissionIncomeExpense"): "fee_and_commission_income_expense",
    ("esef", "ifrs-full:TradingIncomeExpense"): "trading_income_expense",
}

# Whether an ESEF concept is a balance-sheet instant (as-of a date) or an
# income-statement duration (over the fiscal year) - decides which XBRL period
# key to look it up under.
_ESEF_PERIOD_KIND: dict[str, str] = {
    "ifrs-full:Assets": "instant",
    "ifrs-full:Equity": "instant",
    "ifrs-full:InterestRevenueExpense": "duration",
    "ifrs-full:ProfitLoss": "duration",
    "ifrs-full:FeeAndCommissionIncome": "duration",
    "ifrs-full:FeeAndCommissionExpense": "duration",
    "ifrs-full:FeeAndCommissionIncomeExpense": "duration",
    "ifrs-full:TradingIncomeExpense": "duration",
}

# 2026-10-08: generalized from a single hardcoded ESEF period (originally only
# FY2024, Erste-only) to any period this project has fetched - the DuPont work
# needed FY2021 too (38 banks cached) alongside FY2024 (29 banks). `_ESEF_PERIOD`
# stays as a named default (not a hard restriction) for callers that don't care
# which year, e.g. compute_rwa_density's default argument.
_ESEF_PERIOD_END = "2024-12-31"
_ESEF_PERIOD = "202412"


def _period_to_esef_period_end(period: str) -> str:
    """"202412" -> "2024-12-31" - only calendar (Dec 31) fiscal year-ends are
    supported, same assumption as esef_client.py and waves.py (task 1.5)."""
    if len(period) != 6 or period[4:] != "12":
        raise ValueError(f"only December year-end periods are supported, got {period!r}")
    return f"{period[:4]}-12-31"


def _esef_period_end_to_period(period_end: str) -> str:
    """"2024-12-31" -> "202412\""""
    return period_end[:4] + period_end[5:7]


def _cached_esef_periods(bank_lei: str) -> list[str]:
    """Which ESEF period_ends (YYYY-MM-DD) are already cached on disk for this bank -
    a local-cache listing, not a live filings.xbrl.org query. Used when `period` is
    None, so "give me everything" means everything this project has actually
    fetched, not a live discovery of every period that might exist."""
    esef_dir = _ROOT / "data" / "raw" / "esef" / bank_lei
    if not esef_dir.exists():
        return []
    return sorted(p.name for p in esef_dir.iterdir() if p.is_dir())

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
    if period is not None:
        try:
            period_ends = [_period_to_esef_period_end(period)]
        except ValueError:
            return []  # not a December year-end - this module can't serve it, see docstring
    else:
        period_ends = _cached_esef_periods(bank_lei)  # "give me everything" = everything cached

    rows: list[dict] = []
    for period_end in period_ends:
        our_period = _esef_period_end_to_period(period_end)
        try:
            facts = esef_client.fetch_facts(bank_lei, period_end)
        except esef_client.EsefNotFoundError:
            rows.append({
                "bank_lei": bank_lei, "period": our_period, "standardized_concept": concept,
                "source_reporting_item": item_code, "source": "esef",
                "provenance": None, "value": None, "status": "missing_from_source",
                "origin_reference": f"ESEF (filings.xbrl.org), {bank_lei}, no filing for {period_end}",
            })
            continue
        except esef_client.EsefDataError as exc:
            raise DataSourceError(str(exc)) from exc

        duration_key, instant_key = esef_client.fiscal_year_keys(period_end)
        period_key = instant_key if _ESEF_PERIOD_KIND[item_code] == "instant" else duration_key
        value = esef_client.get_concept_value(facts, item_code, period_key)
        filing = esef_client.find_filing(bank_lei, period_end)

        if value is None:
            rows.append({
                "bank_lei": bank_lei, "period": our_period, "standardized_concept": concept,
                "source_reporting_item": item_code, "source": "esef",
                "provenance": None, "value": None, "status": "missing_from_source",
                "origin_reference": f"ESEF filing {filing.report_url}, concept {item_code} not tagged as a total",
            })
            continue

        rows.append({
            "bank_lei": bank_lei, "period": our_period, "standardized_concept": concept,
            "source_reporting_item": item_code, "source": "esef",
            "provenance": "reported_actual", "value": value / 1_000_000, "status": "ok",
            "origin_reference": f"ESEF filing (FY{period_end[:4]}), {filing.report_url}, concept {item_code}",
        })
    return rows


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


class RwaDensityError(ValueError):
    """RWA density could not be computed for this bank/period - no reported_actual TREA
    row, or no total_assets row, available."""


def compute_rwa_density(bank_lei: str, period: str = _ESEF_PERIOD) -> float:
    """RWA density = total_risk_exposure_amount / total_assets, for one bank/period.

    Homework 5 (2026-10-08): promotes the spike's own one-off, by-hand calculation
    (spike/compare_sources.py) into a real, reusable, tested function - see
    tests/test_reconcile.py's test_rwa_density_uses_reported_actual_trea for the
    externally-sourced expected value this is checked against.

    Deliberately uses ONLY the TREA row tagged `provenance == "reported_actual"`, never
    `restated_actual` - see spike/comparison.md's "RWA density: which numerator?" section
    for the full reasoning. Restated TREA is a CRR3 pro-forma recast for the stress
    test's own forward-looking 3-year horizon; `total_assets` (from ESEF) was never
    recast for CRR3. Pairing a post-2025-rules numerator with a pre-2025-rules
    denominator would silently mix two different capital regimes into one ratio - this
    function refuses to do that by construction, not just by convention (using restated
    TREA for Erste FY2024 gives ~42.5%, a plausible-looking but methodologically
    mismatched number per the spike).

    Raises RwaDensityError if either figure isn't available for this bank/period (no
    ESEF filing cached, or no reported_actual TREA row) - never silently computes a
    density from whichever TREA row happened to be present.
    """
    df = get_financial_data(
        bank_lei, ["total_risk_exposure_amount", "total_assets"], period=period,
    )
    trea = df[
        (df["standardized_concept"] == "total_risk_exposure_amount")
        & (df["provenance"] == "reported_actual")
    ]
    assets = df[df["standardized_concept"] == "total_assets"]
    if trea.empty or trea.iloc[0]["status"] != "ok":
        raise RwaDensityError(
            f"{bank_lei}/{period}: no reported_actual total_risk_exposure_amount available"
        )
    if assets.empty or assets.iloc[0]["status"] != "ok":
        raise RwaDensityError(f"{bank_lei}/{period}: no total_assets available")
    return float(trea.iloc[0]["value"]) / float(assets.iloc[0]["value"])


class DuPontError(ValueError):
    """A DuPont figure (net income, total assets, total equity, or net interest
    income - the one mandatory Total Revenue component) wasn't available for this
    bank/period."""


def _esef_value(df: pd.DataFrame, concept: str) -> float | None:
    rows = df[(df["source"] == "esef") & (df["standardized_concept"] == concept)]
    if rows.empty or rows.iloc[0]["status"] != "ok":
        return None
    return float(rows.iloc[0]["value"])


def compute_total_revenue(bank_lei: str, period: str) -> dict:
    """Total Revenue = net interest income + net fee and commission income + trading
    income (when tagged) - the denominator compute_dupont()'s Asset Utilization ratio
    needs. Not itself a single reported IFRS concept: it's a composite this project
    builds explicitly for the DuPont homework by SUMMING individually-sourced
    components. This is different from the project's usual refusal to derive
    cross-source figures (e.g. net_interest_income is never derived from gross
    interest income/expense across sources - spike/comparison.md's Cause 1): Total
    Revenue is, by definition, an aggregate of several P&L lines from ONE bank's own
    filing, not two sources' competing claims about the same concept.

    All three components come from ESEF specifically (never stress_test), so the
    whole buildup stays on one consistent reporting perimeter - mixing a
    stress-test-sourced NII with ESEF-sourced fee/trading income would silently
    combine two different consolidation scopes, the exact comparability problem the
    spike's Cause 1 investigation found and corrected for net interest income alone.

    Net fee and commission income prefers a direct net tag
    (ifrs-full:FeeAndCommissionIncomeExpense) and falls back to Income - Expense when
    only the gross pair is tagged (confirmed 2026-10-08: 16/29 cached FY2024 banks tag
    net directly, 28/29 have the gross pair - deriving it here is safe because it's
    one bank's own two disclosed figures, not two different banks' or sources').

    Trading income is included ONLY when the IFRS standard tag
    (ifrs-full:TradingIncomeExpense) is present - confirmed only 9/29 cached FY2024
    banks use it; the rest tag it under their own custom extension taxonomy (e.g.
    bnpp:NetGainOnFinancialInstruments..., san:GainsLossesOnFinancialAssetsAnd...),
    which this project does not attempt to chase per-bank (see CONCEPT_MAP's
    comment - mapping ~20 banks' individual extensions would be exactly the
    curation-cost blowup design.md decision 1 accepted as a non-goal for v1). Decided
    by user (2026-10-08, PLANNING_LOG.md): include it where available rather than drop
    it entirely, with the gap flagged explicitly via the returned `complete` field -
    never silently treated as zero for the banks missing it.

    Returns {"value": float (EUR millions), "complete": bool, "components": dict}.
    `complete` is False whenever the fee or trading component couldn't be determined
    - callers comparing Asset Utilization/Profit Margin across banks should check it
    rather than assume every bank's Total Revenue was built from the same inputs.
    Raises DuPontError if net interest income itself is unavailable (the one
    mandatory component - a bank with no NII figure isn't a meaningful subject here).
    """
    df = get_financial_data(
        bank_lei,
        ["net_interest_income", "fee_and_commission_income", "fee_and_commission_expense",
         "fee_and_commission_income_expense", "trading_income_expense"],
        period=period,
    )
    nii = _esef_value(df, "net_interest_income")
    if nii is None:
        raise DuPontError(f"{bank_lei}/{period}: no ESEF net_interest_income available")

    fee_net = _esef_value(df, "fee_and_commission_income_expense")
    if fee_net is None:
        fee_inc = _esef_value(df, "fee_and_commission_income")
        fee_exp = _esef_value(df, "fee_and_commission_expense")
        if fee_inc is not None and fee_exp is not None:
            fee_net = fee_inc - fee_exp

    trading = _esef_value(df, "trading_income_expense")

    total = nii + (fee_net or 0.0) + (trading or 0.0)
    return {
        "value": total,
        "complete": fee_net is not None and trading is not None,
        "components": {
            "net_interest_income": nii,
            "net_fee_and_commission_income": fee_net,
            "trading_income": trading,
        },
    }


@dataclass(frozen=True)
class DuPontResult:
    bank_lei: str
    period: str
    net_income: float
    total_assets: float
    total_equity: float
    total_revenue: float
    revenue_complete: bool
    profit_margin: float
    asset_utilization: float
    equity_multiplier: float
    roa: float
    roe: float


def compute_dupont(bank_lei: str, period: str) -> DuPontResult:
    """3-factor bank DuPont decomposition:

        ROE = Profit Margin x Asset Utilization x Equity Multiplier
            = (Net Income / Total Revenue) x (Total Revenue / Total Assets)
              x (Total Assets / Total Equity)

    Adapted from a university DuPont-analysis Excel template (a 2008/2009 Hungarian
    banking-sector comparison built on local-GAAP line items - "rendkivuli
    eredmeny"/extraordinary items, detailed interest-income sub-categories - that
    don't exist in IFRS/ESEF taxonomies, for 11 banks' Hungarian subsidiaries this
    project doesn't track). This function keeps the template's core 3-factor ratio
    structure (its own rows 66-69: ROE / leverage / ROA / profit margin) applied to
    this project's actual IFRS/XBRL data and tracked banks, per explicit user
    decision 2026-10-08 (PLANNING_LOG.md) - not the template's Hungarian-GAAP line
    items or its 11-bank Hungarian leaderboard, neither of which this project's data
    can support.

    Uses POINT-IN-TIME (year-end) total_assets/total_equity, NOT the template's own
    average-of-four-quarters methodology - this project has one annual ESEF snapshot
    per bank/year, not intra-year quarterly balance sheets, so a true average isn't
    computable from what's actually available. Flagged here rather than silently
    approximated as if it were the same thing.

    Net income and all Total Revenue components come from ESEF (never stress_test),
    keeping the whole decomposition on one consistent reporting perimeter - see
    compute_total_revenue()'s docstring for why that matters.

    Raises DuPontError if net income, total assets, or total equity aren't available,
    or if compute_total_revenue() can't find net interest income. The result's
    `revenue_complete` field carries through compute_total_revenue()'s own
    completeness flag - check it before comparing profit_margin/asset_utilization
    across banks as if every one's Total Revenue were built from the same inputs.
    """
    df = get_financial_data(
        bank_lei, ["profit_or_loss_for_the_year", "total_assets", "total_equity"], period=period,
    )
    net_income = _esef_value(df, "profit_or_loss_for_the_year")
    total_assets = _esef_value(df, "total_assets")
    total_equity = _esef_value(df, "total_equity")
    if net_income is None:
        raise DuPontError(f"{bank_lei}/{period}: no ESEF profit_or_loss_for_the_year available")
    if total_assets is None:
        raise DuPontError(f"{bank_lei}/{period}: no total_assets available")
    if total_equity is None:
        raise DuPontError(f"{bank_lei}/{period}: no total_equity available")

    revenue = compute_total_revenue(bank_lei, period)
    total_revenue = revenue["value"]

    profit_margin = net_income / total_revenue
    asset_utilization = total_revenue / total_assets
    equity_multiplier = total_assets / total_equity
    roa = net_income / total_assets
    roe = profit_margin * asset_utilization * equity_multiplier

    return DuPontResult(
        bank_lei=bank_lei, period=period, net_income=net_income,
        total_assets=total_assets, total_equity=total_equity,
        total_revenue=total_revenue, revenue_complete=revenue["complete"],
        profit_margin=profit_margin, asset_utilization=asset_utilization,
        equity_multiplier=equity_multiplier, roa=roa, roe=roe,
    )
