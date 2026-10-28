"""Package surface: given a bank + reporting period(s) + requested concepts, return
a reconciled pandas DataFrame of standardized financial/regulatory figures, each
tagged with enough source/provenance metadata to check it against the original
publication (see openspec/specs/data-retrieval/spec.md).

Three real, verified sources are wired in:

- EBA EU-wide Stress Test 2025 bulk CSV (eba_exercises.py, exercise="stress_test").
  Its TRA_SUM template (inside TRA_OTH.csv) reports a mix of P&L and
  regulatory-capital concepts under several "Scenario" codes - confirmed via that
  download's own Metadata_TR.xlsx ("Scenario" sheet): 1 = Actual figures (the
  pre-stress-test starting point, a reported actual), 2 = Baseline projection,
  3 = Adverse projection (both scenario-projected), 11 = Restated.
- ESEF financial statements via filings.xbrl.org (esef_client.py) - one bank's own
  filing for one fiscal year, IFRS-taxonomy-tagged balance-sheet and
  income-statement concepts, all `reported_actual`.
- EBA Pillar 3 Data Hub (P3DH) - see `_p3dh_rows()`'s own docstring for exactly
  what's read and why it's cache-only (never a live P3DH query from inside
  this function). `data/modules.txt` lists all 114 real templates P3DH offers
  (scraped 2026-10-12, see extend-p3dh-template-coverage), but only a few are
  actually wired here - each one inspected against a real export first, never
  wired from its name alone (see that change's design.md):
  - EU KM1 "Key metrics" (2026-10-11): cet1_capital, cet1_ratio,
    total_risk_exposure_amount - a genuine third source for concepts the
    stress test already reports - plus 5 genuinely new concepts the stress
    test doesn't cover at all (2026-10-12): tier1_capital, total_capital,
    leverage_ratio, liquidity_coverage_ratio, nsfr_ratio.
  - EU LI1 "Differences between the accounting scope and the scope of
    prudential consolidation..." (2026-10-12): only its two clean TOTAL rows
    are wired (Total Liabilities, Total shareholders' equity), each split by
    the template's own "a" (accounting scope) / "b" (prudential scope)
    columns - giving a third source for total_equity (column "a", same basis
    as ESEF's), plus three genuinely new concepts
    (total_equity_prudential_scope, total_liabilities,
    total_liabilities_prudential_scope). LI1's other ~60 line items
    (a full accounting-vs-prudential reconciliation per balance-sheet
    category) are deliberately NOT wired - that's a much larger, differently
    shaped undertaking than this module's per-item CONCEPT_MAP fits without
    its own design pass.
  - EU OV1 "Overview of total risk exposure amounts" (2026-10-12): breaks
    KM1's single TREA total down by risk type - credit_risk_rwa,
    counterparty_credit_risk_rwa, cva_risk_rwa, market_risk_rwa,
    operational_risk_rwa, all genuinely new, plus its own "29. Total" row
    mapped to the SAME total_risk_exposure_amount concept KM1 already
    provides (see CONCEPT_MAP's OV1 comment for the real ~1.5% gap between
    the two independently-disclosed totals this surfaces, not yet explained).
  - EU CQ3 "Credit quality of performing and non-performing exposures by past
    due days" (2026-10-12): performing_exposures/non_performing_exposures,
    feeding `compute_npl_ratio()`. A structural wrinkle neither KM1 nor LI1
    had - its `Row` codes repeat across 3 internal sub-sheets, so these are
    matched by `Row Name` instead (still a fixed EBA caption, confirmed
    identical across two banks - see CONCEPT_MAP's CQ3 comment).
  - EU CC1 "Composition of regulatory own funds" (`K_66.01`) was inspected
    and confirmed KM1-shaped (94 fixed row codes, no per-filer vocabulary) but
    deliberately NOT wired - it's a detailed capital-adjustment breakdown that
    would need its own curation pass to pick which of 94 rows matter, the
    same reason most of LI1's line items stayed unwired.

Two of the standardized concepts (net_interest_income,
profit_or_loss_for_the_year) are reported by BOTH the stress test and ESEF for
the same bank and period; three more (cet1_ratio, cet1_capital,
total_risk_exposure_amount) are now reported by BOTH the stress test and P3DH,
and total_equity by BOTH ESEF and P3DH - each source's own figure is returned
as its own row, never combined into one value (spec's "Multiple sources report
the same concept" scenario). total_assets remains ESEF-only; the P3DH-only
concepts (total_equity_prudential_scope, total_liabilities,
total_liabilities_prudential_scope) have no equivalent in either other source.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import openpyxl
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
    # Added 2026-10-11: EU KM1 ("K_61.00 - EU KM1 - Key metrics template") row codes,
    # confirmed against Erste Group Bank AG's own cached exports - see _p3dh_rows()'s
    # docstring for the cross-check against the stress test's independent figure for
    # the same bank/period that validated both the row mapping and the unit/period
    # handling below. Item code format: "<template>::Row=<row code>::<column code>" -
    # column "0010" is EU KM1's "a. T" (current reference date), see _p3dh_rows().
    ("p3dh", "K_61.00::Row=0010::0010"): "cet1_capital",
    ("p3dh", "K_61.00::Row=0020::0010"): "tier1_capital",
    ("p3dh", "K_61.00::Row=0030::0010"): "total_capital",
    ("p3dh", "K_61.00::Row=0040::0010"): "total_risk_exposure_amount",
    ("p3dh", "K_61.00::Row=0050::0010"): "cet1_ratio",
    # Added 2026-10-12: same template, 3 more rows - all decimal fractions already
    # (confirmed on Erste's own export: leverage ratio 0.0823, LCR 1.4824, NSFR 1.4220 -
    # i.e. 8.23%/148.24%/142.20%), so _P3DH_RATIO_CONCEPTS below, not a unit conversion.
    ("p3dh", "K_61.00::Row=0220::0010"): "leverage_ratio",
    ("p3dh", "K_61.00::Row=0320::0010"): "liquidity_coverage_ratio",
    ("p3dh", "K_61.00::Row=0350::0010"): "nsfr_ratio",
    # Added 2026-10-12: EU LI1 ("K_64.01 - EU LI1 - Differences between the accounting
    # scope and the scope of prudential consolidation..."). Unlike EU KM1 (fixed row
    # codes), LI1's ~60 line items are identified by an "Open Key" breakdown-member
    # string, not a Row code - item code format here is
    # "<template>::Open Key=<open key string>::<column code>". Only the template's two
    # genuinely clean TOTAL rows are wired, not its full line-item breakdown (deliberate
    # scope choice, see reconcile.py's module docstring) - column "0010" is "a. Carrying
    # values as reported in published financial statements" (accounting scope, the
    # SAME basis ESEF's own total_equity reports - confirmed against Erste's own
    # export, see _p3dh_rows()'s docstring), column "0020" is "b. Carrying values
    # under scope of prudential consolidation" (a genuinely new concept - exactly the
    # comparability-risk distinction README section 5 describes, not available from
    # any other wired source). Checked 2026-10-13 (gap-li1-line-items) against all 36
    # pilot banks with a cached export, not just Erste/BNP Paribas: these two Open
    # Keys are NOT typical - only 1/36 (Erste) has BOTH; only 4/36 have ANY row
    # containing "total" at all, and those don't agree on scope (BNP has asset/
    # liability totals but no equity total; KBC has only an asset total; Deutsche
    # Bank's "total" rows are unrelated fair-value sub-totals). Expect
    # missing_from_source for roughly 35 of 36 pilot banks on these 3 P3DH-only
    # concepts - Erste's full coverage is the outlier, not representative. No other
    # Open Key comes anywhere close to full-pilot coverage either (the most common
    # label, "Other liabilities", is only 23/36) - confirms none of LI1's other line
    # items are safe to wire, this time checked systematically rather than assumed
    # from the 2-bank BNP comparison alone. See DATA_SOURCES_NOTES.md's 2026-10-13
    # entry for the full frequency breakdown.
    ("p3dh", "K_64.01::Open Key=Type of liabilities = Total shareholders' equity::0010"): "total_equity",
    ("p3dh", "K_64.01::Open Key=Type of liabilities = Total shareholders' equity::0020"): "total_equity_prudential_scope",
    ("p3dh", "K_64.01::Open Key=Type of liabilities = Total Liabilities::0010"): "total_liabilities",
    ("p3dh", "K_64.01::Open Key=Type of liabilities = Total Liabilities::0020"): "total_liabilities_prudential_scope",
    # Added 2026-10-12 (extend-p3dh-template-coverage): EU OV1 ("K_60.00 - EU OV1 -
    # Overview of total risk exposure amounts") - confirmed KM1-shaped on Erste's own
    # export: 34 fixed, globally-unique row codes, no per-filer vocabulary. Breaks the
    # single TREA total KM1 already reports down by risk type. Row 0380's own "29.
    # Total" maps to the SAME total_risk_exposure_amount concept KM1's row 0040
    # already provides - deliberately, not a mistake: confirmed on Erste's own
    # 2025-12-31 data that the two independently-disclosed totals do NOT match
    # exactly (OV1: 149,673.86 EUR m; KM1: 147,487.07 EUR m - a real ~1.5% gap, not
    # yet explained), which this module's design surfaces as two untagged-as-one
    # rows for the same concept/period/source rather than silently picking one or
    # averaging them (the exact "Multiple sources report the same concept" behavior
    # the rest of this module already follows for stress_test vs. ESEF/P3DH).
    ("p3dh", "K_60.00::Row=0010::0010"): "credit_risk_rwa",
    ("p3dh", "K_60.00::Row=0070::0010"): "counterparty_credit_risk_rwa",
    ("p3dh", "K_60.00::Row=0120::0010"): "cva_risk_rwa",
    ("p3dh", "K_60.00::Row=0260::0010"): "market_risk_rwa",
    ("p3dh", "K_60.00::Row=0320::0010"): "operational_risk_rwa",
    ("p3dh", "K_60.00::Row=0380::0010"): "total_risk_exposure_amount",
    # Added 2026-10-12 (extend-p3dh-template-coverage): EU CQ3 ("K_82.00 - EU CQ3:
    # Credit quality of performing and non-performing exposures by past due days").
    # A real structural wrinkle neither KM1 nor LI1 had: this template's `Row` codes
    # are NOT globally unique - they're reused across 3 internal sub-sheets (on-
    # balance-sheet items, off-balance-sheet items, and a grand-total sheet), only
    # disambiguated by `Row Name`'s text (confirmed via the `Cell` field's own
    # ".a"/".b"/".c" sub-sheet prefix - matching on `Row` alone would have silently
    # picked whichever sub-sheet's row happened to be found first). `Row Name` itself
    # is still a fixed, EBA-numbered caption ("220 Total"), not per-filer prose like
    # LI1's Open Key - confirmed identical wording on a second bank (BNP Paribas)
    # before trusting it, per this change's own design rule. Reuses
    # `_read_p3dh_fact()`'s existing generic field-matching unchanged (`match_field`
    # can be any real header name, "Row Name" included) - no new code needed, only
    # these entries, exactly as design.md predicted. Feeds compute_npl_ratio().
    ("p3dh", "K_82.00::Row Name= 220 Total::0010"): "performing_exposures",
    ("p3dh", "K_82.00::Row Name= 220 Total::0040"): "non_performing_exposures",
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

# 2026-10-08: generalized from a single hardcoded ESEF period (originally only
# FY2024, Erste-only) to any period this project has fetched - cross-period analysis
# work needed FY2021 too (38 banks cached) alongside FY2024 (29 banks). `_ESEF_PERIOD`
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


# Which standardized concepts are already decimal fractions (no EUR->EUR-millions
# conversion needed) - everything else read from P3DH is a balance-sheet/capital amount.
_P3DH_RATIO_CONCEPTS = frozenset({"cet1_ratio", "leverage_ratio", "liquidity_coverage_ratio", "nsfr_ratio"})


def _p3dh_entity_name(bank_lei: str) -> str | None:
    return next((e.name for e in load_entities() if e.lei == bank_lei), None)


def _cached_p3dh_files(bank_name: str, template_prefix: str) -> list[Path]:
    """Matches run_update.py's actual on-disk naming (edap_scraper.export_data_points):
    "<entity name, spaces/slashes replaced>_<template prefix>*.xlsx" directly under
    data/raw/ - a local-cache listing, never a live P3DH query."""
    safe_name = bank_name.replace(" ", "_").replace("/", "-")
    return sorted((_ROOT / "data" / "raw").glob(f"{safe_name}_{template_prefix}*.xlsx"))


def _row_cell(row: tuple, idx: dict[str, int], name: str):
    """openpyxl's read_only iter_rows() trims a row's tuple to its last non-empty
    cell, so a row whose trailing columns are genuinely blank (confirmed on BNP
    Paribas's own LI1 export) is SHORTER than the header - a plain row[i] would
    raise IndexError on those columns rather than reading them as blank. Extracted
    to module level (homework 6 review 8) so this bounds-checking logic has a direct
    unit test with hand-built tuples, not only indirect coverage through whichever
    bank's cached export happens to still have a short row today."""
    i = idx[name]
    return row[i] if i < len(row) else None


def _read_p3dh_fact(
    path: Path, match_field: str, match_value: str, column_code: str
) -> tuple[datetime, str | None, str | None, float | None]:
    """Pulls one (ReferenceDate, row/member description, column description, FactValue)
    out of a cached P3DH Data Points Report export - row 1 carries ReferenceDate, row 2
    is the real header, data rows follow (see module docstring). `match_field` is
    whichever of that header's own column names actually identifies a fact
    bank-independently for the template at hand - "Row" for EU KM1/EU OV1's fixed,
    EBA-standardized row codes; "Open Key" for EU LI1's breakdown-member strings
    (that template has no row code of its own, see CONCEPT_MAP's LI1 comment);
    "Row Name" for EU CQ3, where `Row` alone is ambiguous (reused across its 3
    internal sub-sheets) but the Row Name caption is still bank-independent (see
    CONCEPT_MAP's CQ3 comment) - deliberately generic rather than special-cased per
    template, since a template not yet inspected may need yet another one of its
    own real header columns as the safe match key.

    The last three return values are None, not an exception, when the fact genuinely
    isn't in this export: confirmed real on BNP Paribas's own LI1 file, which has no
    "Total shareholders' equity" Open Key at all (it maps its own chart-of-accounts
    categories into LI1 differently than Erste does) - unlike EU KM1's row codes,
    EU LI1's Open Key strings are each filer's OWN vocabulary, not a fixed EBA-wide
    list, so "not found" there is a genuine, expected per-bank difference, never
    evidence the file itself is malformed. DataSourceError is still raised for an
    actual read/parse failure (a corrupt file, or one missing ReferenceDate/the
    expected header row entirely) - that distinction is why this doesn't just return
    None to mean "nothing usable" across the board."""
    import warnings

    try:
        with warnings.catch_warnings():
            # P3DH's own export doesn't set a default cell style - harmless, openpyxl
            # applies its own default; silenced so it doesn't look like a real problem
            # on every single file read.
            warnings.filterwarnings("ignore", message="Workbook contains no default style")
            wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        ws = wb.worksheets[0]
        rows_iter = ws.iter_rows(values_only=True)
        header1 = next(rows_iter)
        reference_date = next((c for c in header1 if isinstance(c, datetime)), None)
        if reference_date is None:
            raise DataSourceError(f"{path}: no ReferenceDate found in row 1 - malformed export?")
        header2 = next(rows_iter)
        idx = {name: i for i, name in enumerate(header2)}
        for required in ("Row", "Open Key", "Column", "Column Name", "Row Name", "FactValue"):
            if required not in idx:
                raise DataSourceError(f"{path}: expected header {required!r} not found - malformed export?")

        def cell(r: tuple, name: str):
            return _row_cell(r, idx, name)

        for r in rows_iter:
            if cell(r, match_field) == match_value and cell(r, "Column") == column_code:
                fact_value = cell(r, "FactValue")
                if fact_value is None:
                    continue  # this exact (member, column) combination is genuinely blank
                row_desc = cell(r, "Row Name")
                description = str(row_desc).strip() if row_desc is not None else match_value
                column_desc = str(cell(r, "Column Name") or "").strip()
                return reference_date, description, column_desc, float(fact_value)
    except (OSError, KeyError, StopIteration, ValueError) as exc:
        raise DataSourceError(f"failed to read {path}: {exc}") from exc
    return reference_date, None, None, None


def _scale_p3dh_amount(raw_value: float) -> float:
    """Converts a non-ratio P3DH FactValue to EUR millions, matching this module's
    convention - but P3DH's raw exports are NOT uniformly scaled across filers,
    confirmed 2026-10-28 while checking RWA density for the dashboard's concept picker:
    Erste's own K_61.00 TREA FactValue is 147487065101.15 (plain EUR, needs /1e6 to
    become a plausible 147487.07 EUR-m), but La Banque Postale's is 100031 for the same
    row/column - already EUR-m-scale (matches the EBA stress test's own independent
    ~101,260-104,427 figure for the same bank/period; dividing it by 1e6 again gave a
    nonsense 0.100031). The raw export carries no unit/scale column at all (confirmed -
    only Entity/Template/Row/Column/FactValue), so there's no metadata to read instead of
    guessing. No real EU bank in this project's scope has total capital, RWA, liabilities,
    etc. below roughly EUR 1m, so a post-division result under 1.0 is itself the signal
    that the raw value was already EUR-m-scale, not EUR-scale - this is a plausibility
    guard, not a certainty, but a division that lands under 1.0 for one of these concepts
    is never a real answer either way."""
    scaled = raw_value / 1_000_000
    return raw_value if abs(scaled) < 1.0 else scaled


def _p3dh_rows(bank_lei: str, concept: str, item_code: str, period: str | None) -> list[dict]:
    """item_code is "<template prefix>::<Row or Open Key>=<match value>::<column code>",
    e.g. "K_61.00::Row=0010::0010" for EU KM1's CET1 capital row, or
    "K_64.01::Open Key=Type of liabilities = Total shareholders' equity::0020" for EU
    LI1's prudential-scope equity total. Reads cached P3DH Data Points Report exports
    only - run_update.py (via edap_scraper's real Playwright export) is the only thing
    that ever triggers a live P3DH fetch; unlike esef_client.fetch_facts (a cheap bulk
    JSON download), triggering a ~15-30s headless-browser scrape as a side effect of a
    DataFrame call would make this function slow and flaky in a way none of its other
    sources are, so get_financial_data() deliberately returns nothing for a bank/template
    run_update.py hasn't fetched yet, rather than scrape on demand. This is a real,
    documented asymmetry versus esef_client/eba_exercises, not an oversight.

    For EU KM1, CONCEPT_MAP only ever uses column "0010" ("a. T", the figure as of the
    export's own reference date), even though every export also discloses the same
    metric's previous four quarters (T-1..T-4). Deliberately not read: (1) a bank with
    several cached reference dates would otherwise produce multiple overlapping,
    near-duplicate rows for the same real calendar quarter (that quarter's own "T" value
    from its own file, plus every later file's backward-looking echo of the same
    figure), and (2) a later file's lookback column could silently carry a RESTATED
    figure for an earlier quarter with no way to tag it as a restatement (unlike the
    stress test's own explicit Scenario 11 "Restated" code) - using only "T" means every
    KM1 row this function returns is the figure originally filed for its own reference
    date. EU LI1 has no such lookback columns - its "0010"/"0020" are two DIFFERENT
    concepts (accounting scope vs. prudential scope), not a time series, so both are
    legitimately read.

    Capital/exposure/balance-sheet amounts convert EUR -> EUR millions, matching this
    module's existing convention; concepts in `_P3DH_RATIO_CONCEPTS` are left as decimal
    fractions, already matching stress_test's cet1_ratio. Confirmed,
    not assumed: Erste Group Bank AG's 2025-12-31 KM1 export's own T-4 column
    (2024-12-31, for cross-check only - not what this function reads) gives
    cet1_capital 23995.665 (EUR m) and cet1_ratio 0.152605 against the stress test's
    independently reported_actual figures for the exact same bank/period, 23995.673 and
    0.152605 - matching almost exactly, which validated both the unit conversion and the
    reference-date -> period mapping before trusting either. The LI1 wiring was checked
    for internal plausibility instead (no ESEF data cached for the same 2025-12-31
    reference date to cross-check against): Erste's own 2025-12-31 LI1 export gives
    Total Liabilities 333,908.98 (EUR m) + Total shareholders' equity 34,665.16 (EUR m)
    = 368,574.14 (EUR m) - a plausible total-assets figure given its FY2024 (ESEF) total
    assets of 353,736m, consistent with continued balance-sheet growth into 2025.
    """
    template_prefix, match_expr, column_code = item_code.split("::")
    match_field, match_value = match_expr.split("=", 1)
    bank_name = _p3dh_entity_name(bank_lei)
    if bank_name is None:
        return []

    rows: list[dict] = []
    for path in _cached_p3dh_files(bank_name, template_prefix):
        reference_date, description, column_desc, raw_value = _read_p3dh_fact(
            path, match_field, match_value, column_code
        )
        our_period = reference_date.strftime("%Y%m")
        if period is not None and our_period != period:
            continue
        if raw_value is None:
            # genuinely not in THIS bank's export (see _read_p3dh_fact's docstring on
            # Open Key being per-filer vocabulary, not a fixed EBA-wide list) - missing
            # from source, never a fabricated value or a processing failure.
            rows.append({
                "bank_lei": bank_lei, "period": our_period, "standardized_concept": concept,
                "source_reporting_item": item_code, "source": "p3dh",
                "provenance": None, "value": None, "status": "missing_from_source",
                "origin_reference": (
                    f"EBA Pillar 3 Data Hub, {bank_name}, template {template_prefix}, "
                    f"{match_field}={match_value!r}/column {column_code!r} not reported in "
                    f"this export, reference date {reference_date.date().isoformat()}"
                ),
            })
            continue
        value = raw_value if concept in _P3DH_RATIO_CONCEPTS else _scale_p3dh_amount(raw_value)
        rows.append({
            "bank_lei": bank_lei, "period": our_period, "standardized_concept": concept,
            "source_reporting_item": item_code, "source": "p3dh",
            "provenance": "reported_actual", "value": value, "status": "ok",
            "origin_reference": (
                f"EBA Pillar 3 Data Hub, {bank_name}, template {template_prefix}, "
                f"{description} ({column_desc}), reference date {reference_date.date().isoformat()}"
            ),
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
            elif source == "p3dh":
                rows.extend(_p3dh_rows(bank_lei, concept, item_code, period))
    return pd.DataFrame(rows, columns=_DATAFRAME_COLUMNS)


class RwaDensityError(ValueError):
    """RWA density could not be computed for this bank/period - no reported_actual TREA
    row, no total_assets row, or (see _EUR_FX_RATES) no EUR conversion available for the
    currency total_assets was reported in."""


# ECB reference rates, EUR base, fetched 2026-10-28 (see PLANNING_LOG.md's same-day
# entry). total_risk_exposure_amount (from P3DH/the EBA stress test) is always EUR, but
# total_assets (from ESEF) is reported in each filer's OWN currency - confirmed real for
# 4 pilot banks (Danske Bank/DKK, DNB/NOK, SEB/SEK, Svenska Handelsbanken/SEK). Dividing
# a EUR numerator by a raw DKK/NOK/SEK denominator silently produced a nonsense ratio
# (confirmed: Danske Bank's density read 2.93% instead of a real ~22%) - caught 2026-10-28
# while checking real coverage for the dashboard's concept picker, not by a test, since
# no existing test exercised a non-EUR bank. Not live-fetched, to keep this function's
# existing dependency-free, cache-only character (same reasoning as P3DH being
# cache-only - see _p3dh_rows's docstring); a rate a few months stale changes the result
# by at most a percent or two for these currencies, acceptable for this purpose but worth
# refreshing periodically.
_EUR_FX_RATES = {"DKK": 7.4741, "NOK": 10.3475, "SEK": 11.0560}


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

    total_assets is converted to EUR first if the filer reported it in another currency
    (see _EUR_FX_RATES) - get_financial_data()'s own DataFrame doesn't expose a filing's
    currency (a known, documented gap), so this reads it directly off the cached ESEF
    facts rather than assume EUR.

    Raises RwaDensityError if either figure isn't available for this bank/period (no
    ESEF filing cached, or no reported_actual TREA row), or if total_assets was reported
    in a currency this function has no EUR rate for - never silently computes a density
    from whichever TREA row happened to be present, or from a wrong-currency ratio.
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

    assets_value = float(assets.iloc[0]["value"])
    period_end = _period_to_esef_period_end(period)
    facts = esef_client.fetch_facts(bank_lei, period_end)
    _, instant_key = esef_client.fiscal_year_keys(period_end)
    unit = esef_client.get_concept_unit(facts, "ifrs-full:Assets", instant_key)
    currency = (unit or "iso4217:EUR").rsplit(":", 1)[-1]
    if currency != "EUR":
        if currency not in _EUR_FX_RATES:
            raise RwaDensityError(
                f"{bank_lei}/{period}: total_assets reported in {currency}, "
                f"no EUR conversion rate available for it"
            )
        assets_value = assets_value / _EUR_FX_RATES[currency]

    return float(trea.iloc[0]["value"]) / assets_value


class NplRatioError(ValueError):
    """Gross NPL ratio could not be computed for this bank/period - no cached EU CQ3
    data (performing_exposures/non_performing_exposures) available."""


def compute_npl_ratio(bank_lei: str, period: str) -> float:
    """Gross non-performing-loans ratio = non_performing_exposures /
    (performing_exposures + non_performing_exposures), for one bank/period - both
    concepts from EU CQ3's own grand-total sub-sheet (reconcile._p3dh_rows, added
    2026-10-12, extend-p3dh-template-coverage). Confirmed plausible on real data
    before trusting the mapping: Erste 2025-12-31 gives ~1.42%, BNP Paribas
    2025-12-31 gives ~1.51% - both in the normal range for a strong European bank,
    not a tagging artifact.

    Raises NplRatioError if either figure isn't cached for this bank/period, same
    "never silently compute from a partial result" discipline as
    compute_rwa_density - P3DH is cache-only (see _p3dh_rows()'s docstring), so a
    missing figure here means "not yet fetched for this bank/period", not "EU CQ3
    reports zero credit exposure".
    """
    df = get_financial_data(bank_lei, ["performing_exposures", "non_performing_exposures"], period=period)
    performing = df[df["standardized_concept"] == "performing_exposures"]
    non_performing = df[df["standardized_concept"] == "non_performing_exposures"]
    if performing.empty or performing.iloc[0]["status"] != "ok":
        raise NplRatioError(f"{bank_lei}/{period}: no performing_exposures available")
    if non_performing.empty or non_performing.iloc[0]["status"] != "ok":
        raise NplRatioError(f"{bank_lei}/{period}: no non_performing_exposures available")
    performing_value = float(performing.iloc[0]["value"])
    non_performing_value = float(non_performing.iloc[0]["value"])
    return non_performing_value / (performing_value + non_performing_value)

