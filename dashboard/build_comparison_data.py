"""Precomputes one display value per (bank, metric) for all 28 pilot banks x 24
picker concepts, FY2025 / 2025-12-31, into a single JSON the dashboard embeds - the
results view has no live Python backend, so this has to happen ahead of time.

Run from the repo root: python dashboard/build_comparison_data.py

Monkeypatches esef_client.find_filing() to a dummy that never hits the network: every
pilot bank's FY2025 ESEF facts are already cached locally (confirmed before writing
this script), and reconcile._esef_rows() calls find_filing() unconditionally just to
build a human-readable origin_reference URL this script doesn't use - without the
patch, that call alone triggers filings.xbrl.org's 429 rate limit on nearly every
request. get_financial_data()/compute_rwa_density()/compute_cost_to_income_ratio()/
compute_npl_ratio() are otherwise used completely unmodified, so every value here
goes through the exact same tested logic as the rest of the package.
"""
import json
import os

from data_acquisition import esef_client, reconcile

esef_client.find_filing = lambda lei, period_end: esef_client.EsefFiling(
    lei=lei, period_end=period_end, json_url="cached", report_url="cached",
)

HERE = os.path.dirname(os.path.abspath(__file__))
PERIOD = "202512"
LEIS_PATH = os.path.join(HERE, "pilot_28_leis.json")
OUT_PATH = os.path.join(HERE, "comparison_data.json")

with open(LEIS_PATH, encoding="utf-8") as f:
    LEIS = json.load(f)

# (concept_id, kind) - "amount" values are EUR millions (converted if the filer
# reported in another currency), "ratio" values are fractions (display as %).
METRICS = [
    ("cet1_capital", "amount"),
    ("cet1_ratio", "ratio"),
    ("tier1_capital", "amount"),
    ("total_capital", "amount"),
    ("total_risk_exposure_amount", "amount"),
    ("leverage_ratio", "ratio"),
    ("rwa_density", "ratio"),
    ("total_assets", "amount"),
    ("total_equity", "amount"),
    ("net_interest_income", "amount"),
    ("net_fee_income", "amount"),
    ("total_revenue", "amount"),
    ("cost_to_income_ratio", "ratio"),
    ("profit_or_loss_for_the_year", "amount"),
    ("credit_risk_rwa", "amount"),
    ("counterparty_credit_risk_rwa", "amount"),
    ("cva_risk_rwa", "amount"),
    ("market_risk_rwa", "amount"),
    ("operational_risk_rwa", "amount"),
    ("liquidity_coverage_ratio", "ratio"),
    ("nsfr_ratio", "ratio"),
    ("performing_exposures", "amount"),
    ("non_performing_exposures", "amount"),
    ("npl_ratio", "ratio"),
]
RAW_CONCEPTS = [c for c, _ in METRICS if c not in ("rwa_density", "cost_to_income_ratio", "npl_ratio")]

_PROVENANCE_RANK = {"reported_actual": 0, "restated_actual": 1, "scenario_projection": 2}
_SOURCE_RANK = {"esef": 0, "p3dh": 1, "stress_test": 2}
_TEMPLATE_PREFIXES = {"K_61.00": "EU KM1", "K_60.00": "EU OV1"}

# Below this relative gap between two same-tier figures, treat the difference as
# floating-point/export noise rather than a real disagreement (e.g. EU OV1's own
# TREA total vs EU KM1's, for most banks, agree to 8+ significant digits - only a
# genuine cross-template disagreement, like Erste's real ~1.5% KM1-vs-OV1 gap,
# should be surfaced to the demo rather than silently resolved away).
_DISAGREEMENT_THRESHOLD = 0.001


def _template_label(source_reporting_item):
    item = str(source_reporting_item)
    for prefix, label in _TEMPLATE_PREFIXES.items():
        if item.startswith(prefix):
            return label
    return item


def pick_best_row(df, concept):
    """Returns (picked_row, missing_reason, disagreement) for one concept.

    Collapsing every source down to a single display value is a display-layer
    convenience, not a reconciliation - get_financial_data() itself still returns
    every row untouched. When more than one row at the best-available provenance
    tier genuinely disagrees (not just rounding/export noise), that disagreement
    is surfaced via the returned `disagreement` dict instead of being silently
    hidden behind the precedence pick - this is the whole point of carrying
    source/provenance per figure rather than reconciling into one number.
    """
    rows = df[df["standardized_concept"] == concept]
    ok = rows[rows["status"] == "ok"].copy()
    if ok.empty:
        missing = rows[rows["status"] != "ok"]
        reason = str(missing.iloc[0]["origin_reference"]) if not missing.empty else "Not available from any wired source for this bank/period."
        return None, reason, None

    ok["_prank"] = ok["provenance"].map(lambda p: _PROVENANCE_RANK.get(p, 9))
    best_prank = ok["_prank"].min()
    top = ok[ok["_prank"] == best_prank]

    disagreement = None
    # Only check for a real disagreement at the reported_actual tier. At the
    # scenario_projection tier (used only when no actual figure exists at all),
    # multiple rows are EBA's own baseline/adverse stress scenarios under the
    # same item code - two different projected futures by design, not two
    # sources disagreeing about one reported fact, so they're never surfaced
    # as a "disagreement".
    if best_prank == _PROVENANCE_RANK["reported_actual"] and len(top) >= 2:
        lo, hi = top["value"].min(), top["value"].max()
        if hi != 0 and (hi - lo) / abs(hi) > _DISAGREEMENT_THRESHOLD:
            pct = (hi - lo) / lo * 100
            disagreement = {
                "note": f"Sources disagree by {pct:.1f}%; the package returns every figure, tagged by its own source template, rather than resolving them.",
                "values": [
                    {
                        "value": float(r["value"]),
                        "currency": r["currency"],
                        "label": _template_label(r["source_reporting_item"]),
                        "source": r["source"],
                    }
                    for _, r in top.sort_values("value", ascending=False).iterrows()
                ],
            }

    ok["_srank"] = ok["source"].map(lambda s: _SOURCE_RANK.get(s, 9))
    ok["_irank"] = ok["source_reporting_item"].map(lambda i: 0 if "K_61" in str(i) else 1)
    ok = ok.sort_values(["_prank", "_srank", "_irank"])
    return ok.iloc[0], None, disagreement


def to_eur(value, currency):
    currency = currency or "EUR"
    if currency == "EUR":
        return value
    if currency in reconcile._EUR_FX_RATES:
        return value / reconcile._EUR_FX_RATES[currency]
    return None


result = {}
for i, lei in enumerate(LEIS):
    df = reconcile.get_financial_data(lei, RAW_CONCEPTS, period=PERIOD)
    bank_out = {}
    for concept, kind in METRICS:
        if concept == "rwa_density":
            try:
                bank_out[concept] = {"status": "ok", "value": reconcile.compute_rwa_density(lei, PERIOD)}
            except reconcile.RwaDensityError as exc:
                bank_out[concept] = {"status": "missing", "reason": str(exc)}
            continue
        if concept == "cost_to_income_ratio":
            try:
                bank_out[concept] = {"status": "ok", "value": reconcile.compute_cost_to_income_ratio(lei, PERIOD)}
            except reconcile.CostToIncomeRatioError as exc:
                bank_out[concept] = {"status": "missing", "reason": str(exc)}
            continue
        if concept == "npl_ratio":
            try:
                bank_out[concept] = {"status": "ok", "value": reconcile.compute_npl_ratio(lei, PERIOD)}
            except reconcile.NplRatioError as exc:
                bank_out[concept] = {"status": "missing", "reason": str(exc)}
            continue

        row, reason, disagreement = pick_best_row(df, concept)
        if row is None:
            bank_out[concept] = {"status": "missing", "reason": reason}
            continue
        value = float(row["value"])
        if kind == "amount":
            eur_value = to_eur(value, row["currency"])
            if eur_value is None:
                bank_out[concept] = {
                    "status": "missing",
                    "reason": f"Reported in {row['currency']}, no EUR conversion rate available for it.",
                }
                continue
            cell = {
                "status": "ok", "value": eur_value,
                "provenance": row["provenance"], "source": row["source"],
            }
        else:
            cell = {"status": "ok", "value": value, "provenance": row["provenance"], "source": row["source"]}

        if disagreement:
            if kind == "amount":
                for v in disagreement["values"]:
                    v["value"] = to_eur(v["value"], v["currency"])
            cell["disagreement"] = disagreement
        bank_out[concept] = cell
    result[lei] = bank_out
    print(f"{i+1}/{len(LEIS)} {lei} done")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f)
print("wrote", OUT_PATH)
