# -*- coding: utf-8 -*-
"""Assembles the self-contained dashboard HTML from this folder's inputs
(pilot_28_leis.json, total_assets.json, europe_map.svg, bank_logos/, country_flags/,
comparison_data.json) plus data/entities.csv.

Run from the repo root (after build_comparison_data.py has produced
dashboard/comparison_data.json): python dashboard/build_dashboard.py

The output (docs/dashboard.html) embeds every logo/flag as a base64 data URI rather
than referencing files by path, so the single HTML file has no external
dependencies at all - open it anywhere, no server, no sibling asset folders.
"""
import base64
import csv
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)

ENTITIES = os.path.join(REPO_ROOT, "data", "entities.csv")
SVG_SRC = os.path.join(HERE, "europe_map.svg")
LOGO_DIR = os.path.join(HERE, "bank_logos")
FLAG_DIR = os.path.join(HERE, "country_flags")
TA_PATH = os.path.join(HERE, "total_assets.json")
COMPARISON_DATA_PATH = os.path.join(HERE, "comparison_data.json")
LEIS28_PATH = os.path.join(HERE, "pilot_28_leis.json")
OUT = os.path.join(REPO_ROOT, "docs", "dashboard.html")

BBOXES = {
  "fr": {"cx": 241.24, "cy": 384.29}, "de": {"cx": 309.32, "cy": 324.76},
  "it": {"cx": 330.51, "cy": 437.28}, "dk": {"cx": 316.03, "cy": 262.69},
  "es": {"cx": 190.93, "cy": 452.44}, "gr": {"cx": 441.70, "cy": 466.08},
  "se": {"cx": 344.05, "cy": 186.30}, "ie": {"cx": 170.29, "cy": 278.54},
  "at": {"cx": 332.40, "cy": 365.61}, "fi": {"cx": 388.52, "cy": 146.33},
  "be": {"cx": 262.65, "cy": 331.58}, "no": {"cx": 334.16, "cy": 160.0},
  "pt": {"cx": 137.32, "cy": 446.20}, "nl": {"cx": 269.79, "cy": 311.85},
}

# Visual-only anchor overrides for a cluster's floating card - NOT the country's own
# highlighted shape (that stays geographically real). NL's logo cluster sits too close
# to BE's, making individual logos (e.g. ING) hard to click - moved into Germany's empty
# screen space (Germany has zero banks in the 28-bank set) to give it room.
CLUSTER_ANCHOR_OVERRIDES = {
    "nl": {"cx": 300.0, "cy": 300.0},
}

CATEGORIES = [
    ("Capital & Solvency", [
        ("cet1_capital", "CET1 capital"),
        ("cet1_capital_pct_assets", "CET1 capital (% of assets)"),
        ("cet1_ratio", "CET1 ratio"),
        ("tier1_capital", "Tier 1 capital"),
        ("tier1_capital_pct_assets", "Tier 1 capital (% of assets)"),
        ("tier1_capital_pct_rwa", "Tier 1 capital (% of RWA, Tier 1 ratio)"),
        ("total_capital", "Total capital"),
        ("total_capital_pct_assets", "Total capital (% of assets)"),
        ("total_capital_pct_rwa", "Total capital (% of RWA, Total capital ratio)"),
        ("total_risk_exposure_amount", "Total risk exposure (RWA)"),
        ("leverage_ratio", "Leverage ratio"),
        ("rwa_density", "RWA density (calculated)"),
    ]),
    ("Balance Sheet", [
        ("total_assets", "Total assets"),
        ("total_equity", "Total equity"),
        ("total_equity_pct_assets", "Total equity (% of assets)"),
    ]),
    ("Profitability", [
        ("net_interest_income", "Net interest income"),
        ("net_interest_income_pct_assets", "Net interest income (% of assets)"),
        ("net_fee_income", "Net fee income (16/28 banks)"),
        ("net_fee_income_pct_assets", "Net fee income (% of assets, 16/28 banks)"),
        ("total_revenue", "Total revenue (18/28 banks)"),
        ("total_revenue_pct_assets", "Total revenue (% of assets, 18/28 banks)"),
        ("cost_to_income_ratio", "Cost-to-income ratio (16/28 banks)"),
        ("profit_or_loss_for_the_year", "Profit or loss for the year"),
        ("profit_or_loss_for_the_year_pct_assets", "Profit or loss (% of assets, ROA)"),
        ("profit_or_loss_for_the_year_pct_equity", "Profit or loss (% of equity, ROE)"),
    ]),
    ("RWA Breakdown", [
        ("credit_risk_rwa", "Credit risk RWA"),
        ("credit_risk_rwa_pct_rwa", "Credit risk RWA (% of total RWA)"),
        ("counterparty_credit_risk_rwa", "Counterparty credit risk RWA"),
        ("counterparty_credit_risk_rwa_pct_rwa", "Counterparty credit risk RWA (% of total RWA)"),
        ("cva_risk_rwa", "CVA risk RWA"),
        ("cva_risk_rwa_pct_rwa", "CVA risk RWA (% of total RWA)"),
        ("market_risk_rwa", "Market risk RWA"),
        ("market_risk_rwa_pct_rwa", "Market risk RWA (% of total RWA)"),
        ("operational_risk_rwa", "Operational risk RWA"),
        ("operational_risk_rwa_pct_rwa", "Operational risk RWA (% of total RWA)"),
    ]),
    ("Liquidity", [
        ("liquidity_coverage_ratio", "Liquidity coverage ratio (LCR)"),
        ("nsfr_ratio", "Net stable funding ratio (NSFR)"),
    ]),
    ("Asset Quality", [
        ("performing_exposures", "Performing exposures"),
        ("non_performing_exposures", "Non-performing exposures"),
        ("npl_ratio", "Gross NPL ratio (calculated, 26/28 banks)"),
    ]),
]

FX = {"DKK": 7.4741, "NOK": 10.3475, "SEK": 11.0560}
NONEUR = {
    "MAES062Z21O4RZ2U7M96": "DKK",  # Danske Bank
    "549300GKFG0RYRRQ1414": "NOK",  # DNB
    "F3JS33DEI6XQ4ZBPTN86": "SEK",  # SEB
    "NHBDILHZTYCNBV5UYZ31": "SEK",  # Svenska Handelsbanken
}
FX_DATE = "2026-10-28"


def slugify(name):
    s = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    return s[:60]


def png_data_uri(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


with open(ENTITIES, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
by_lei_entity = {r["lei"]: r for r in rows}

with open(LEIS28_PATH, encoding="utf-8") as f:
    leis28 = set(json.load(f))

with open(TA_PATH, encoding="utf-8") as f:
    ta_rows = json.load(f)
ta_by_lei = {r["lei"]: r for r in ta_rows}

pilot28 = [by_lei_entity[lei] for lei in leis28]

by_country = {}
for r in pilot28:
    by_country.setdefault(r["country"].lower(), []).append(r)

with open(SVG_SRC, encoding="utf-8") as f:
    svg_raw = f.read()
inner_svg = svg_raw.split("<svg", 1)[1].split(">", 1)[1].rsplit("</svg>", 1)[0]

MAP_W = 900
MAP_H = int(MAP_W * 520 / 680)
PAGE_SCALE = MAP_W / 680

flag_cache = {}


def flag_data_uri(iso2):
    if not iso2 or len(iso2) != 2:
        return ""
    iso2 = iso2.lower()
    if iso2 not in flag_cache:
        path = os.path.join(FLAG_DIR, f"{iso2}.png")
        flag_cache[iso2] = png_data_uri(path) if os.path.exists(path) else ""
    return flag_cache[iso2]


bank_data = {}
clusters_json = {}
clusters_html = []
for code, banks in by_country.items():
    bbox = BBOXES.get(code)
    if not bbox:
        continue
    n = len(banks)
    cols = min(4, math.ceil(math.sqrt(n)))
    logo_tags = []
    for b in banks:
        lei = b["lei"]
        slug = slugify(b["name"])
        logo_path = os.path.join(LOGO_DIR, f"{slug}.png")
        logo_src = png_data_uri(logo_path)
        logo_tags.append(
            f'<img class="logo-chip" data-lei="{lei}" src="{logo_src}" title="{b["name"]}">'
        )
        ta = ta_by_lei.get(lei)
        cur = NONEUR.get(lei)
        if ta and ta.get("value") is not None:
            raw_m = ta["value"]
            if cur:
                eur_bn = (raw_m / 1000) / FX[cur]
                note = f"converted from {cur}, ECB ref. rate {FX[cur]:.4f} ({FX_DATE})"
            else:
                eur_bn = raw_m / 1000
                note = None
            bank_data[lei] = {
                "name": b["name"], "country": b["country"].upper(),
                "total_assets_eur_bn": round(eur_bn, 1),
                "currency_note": note,
            }
        else:
            bank_data[lei] = {"name": b["name"], "country": b["country"].upper(), "total_assets_eur_bn": None, "currency_note": None}
    cluster_html = (
        f'<div class="cluster" id="cl-{code}" data-code="{code}" style="--cols:{cols};">'
        + "".join(logo_tags) + "</div>"
    )
    clusters_html.append(cluster_html)
    anchor = CLUSTER_ANCHOR_OVERRIDES.get(code, bbox)
    clusters_json[code] = {
        "cx": bbox["cx"], "cy": bbox["cy"], "n": n,
        "acx": anchor["cx"], "acy": anchor["cy"],
    }

pilot_codes = set(by_country.keys())
country_style_rules = [
    f'#{code} {{ fill: #cdeadd !important; stroke: #2f8a5e !important; stroke-width: 1.2 !important; cursor:pointer; }}'
    for code in pilot_codes
]

# Logo <img> tags above embed each bank's logo as a base64 data URI, so the basket
# bar/results table (which clone a selected logo's `src` from the map) carry it
# forward automatically - no separate lookup needed there.

category_sections_html = []
for cat_name, items in CATEGORIES:
    rows_html = "".join(
        f'<label class="concept-row"><input type="checkbox" class="concept-check" value="{cid}">'
        f'<span>{label}</span></label>'
        for cid, label in items
    )
    cat_ids = ",".join(cid for cid, _ in items)
    category_sections_html.append(
        f'<div class="concept-category">'
        f'<div class="concept-cat-head">'
        f'<span class="cat-name">{cat_name}</span>'
        f'<button type="button" class="cat-toggle" data-ids="{cat_ids}">select all</button>'
        f'</div>{rows_html}</div>'
    )
CONCEPT_CATEGORIES_HTML = "".join(category_sections_html)

CONCEPT_LABELS = {cid: label for _, items in CATEGORIES for cid, label in items}

with open(COMPARISON_DATA_PATH, encoding="utf-8") as f:
    COMPARISON_DATA = json.load(f)

# Precompute each bank's flag data URI once, keyed by country code, and fold it
# into BANK_DATA so the page needs no separate flag-file lookup at runtime.
for lei, d in bank_data.items():
    d["flag_data_uri"] = flag_data_uri(d["country"])

# "Best" highlighting only applies to metrics that are already normalized ratios,
# where a direction is unambiguous regardless of bank size - never to absolute EUR
# amounts (a bigger bank isn't "better", and highlighting its bigger capital/income
# figures would imply that) and never to rwa_density, which has no real "better"
# direction (it's a risk-weighting intensity, not a performance measure).
METRIC_DIRECTION = {
    "cet1_ratio": "up", "leverage_ratio": "up",
    "liquidity_coverage_ratio": "up", "nsfr_ratio": "up",
    "cost_to_income_ratio": "down", "npl_ratio": "down",
}
METRIC_KIND = {cid: kind for cid, kind in [
    ("cet1_capital", "amount"), ("cet1_ratio", "ratio"), ("tier1_capital", "amount"),
    ("total_capital", "amount"), ("total_risk_exposure_amount", "amount"),
    ("leverage_ratio", "ratio"), ("rwa_density", "ratio"), ("total_assets", "amount"),
    ("total_equity", "amount"), ("net_interest_income", "amount"),
    ("net_fee_income", "amount"), ("total_revenue", "amount"),
    ("cost_to_income_ratio", "ratio"), ("profit_or_loss_for_the_year", "amount"),
    ("credit_risk_rwa", "amount"), ("counterparty_credit_risk_rwa", "amount"),
    ("cva_risk_rwa", "amount"), ("market_risk_rwa", "amount"),
    ("operational_risk_rwa", "amount"), ("liquidity_coverage_ratio", "ratio"),
    ("nsfr_ratio", "ratio"), ("performing_exposures", "amount"),
    ("non_performing_exposures", "amount"), ("npl_ratio", "ratio"),
]}

# Derived "standardized against a base" views - computed client-side from
# COMPARISON_DATA's own already-EUR-converted cells (no new source data, no
# duplicated reconcile.py logic). Three denominators, each scoped to where it's a
# standard, unambiguous bank ratio:
#   - % of total assets: income-statement + capital/equity amounts (ROA-style and
#     leverage-style ratios) - NOT the RWA-breakdown or exposure amounts, normally
#     normalized against RWA/total exposures instead.
#   - % of total RWA: Tier 1/total capital (the standard Tier 1 ratio / total
#     capital ratio - CET1 capital deliberately excluded since cet1_ratio, already
#     wired, IS cet1_capital/RWA) and the 5 RWA-breakdown amounts (risk-type
#     composition of total RWA) - NOT income-statement/assets/equity amounts.
#   - % of total equity: just profit for the year - the standard return-on-equity
#     ratio. Like the %-of-assets ratios, deliberately left out of
#     METRIC_DIRECTION: a higher margin against a smaller equity base can reflect
#     more leverage/risk-taking rather than a "better" bank, same reasoning as ROA
#     not being highlighted.
PCT_ASSETS_METRICS = [
    "net_interest_income", "net_fee_income", "total_revenue",
    "profit_or_loss_for_the_year", "cet1_capital", "tier1_capital",
    "total_capital", "total_equity",
]
PCT_RWA_METRICS = [
    "tier1_capital", "total_capital", "credit_risk_rwa",
    "counterparty_credit_risk_rwa", "cva_risk_rwa", "market_risk_rwa",
    "operational_risk_rwa",
]
PCT_EQUITY_METRICS = ["profit_or_loss_for_the_year"]
DERIVED_RATIO = {}
DERIVED_RATIO.update({f"{m}_pct_assets": (m, "total_assets") for m in PCT_ASSETS_METRICS})
DERIVED_RATIO.update({f"{m}_pct_rwa": (m, "total_risk_exposure_amount") for m in PCT_RWA_METRICS})
DERIVED_RATIO.update({f"{m}_pct_equity": (m, "total_equity") for m in PCT_EQUITY_METRICS})
METRIC_KIND.update({cid: "ratio" for cid in DERIVED_RATIO})

html = f"""<!doctype html><html><head><meta charset="utf-8">
<style>
  body {{ margin:0; background:#f4f3ef; font-family: -apple-system, "Segoe UI", sans-serif; }}
  .page {{ max-width:960px; margin:20px auto 140px; }}
  .map-wrap {{
    position: relative; width:{MAP_W}px; height:{MAP_H}px; margin: 0 auto;
    background:#f9f9f7; border:1px solid #e1e0d9; border-radius:10px; overflow:hidden;
  }}
  svg {{ width:{MAP_W}px; height:{MAP_H}px; display:block; }}
  #zoomGroup {{ transition: transform 480ms cubic-bezier(.3,.7,.3,1); transform-origin: 0px 0px; }}
  path {{ stroke:#fff; stroke-width:0.6; }}
  {chr(10).join(country_style_rules)}
  #overlay {{ position:absolute; inset:0; pointer-events:none; }}
  .cluster {{
    position:absolute; transform:translate(-50%,-50%);
    display:grid; grid-template-columns: repeat(var(--cols), 26px);
    gap:3px; padding:3px; background:rgba(255,255,255,0.92);
    border:1px solid rgba(11,11,11,0.12); border-radius:6px;
    box-shadow:0 1px 4px rgba(0,0,0,0.12);
    transition: opacity 220ms ease;
    pointer-events:auto;
  }}
  .logo-chip {{
    width:26px; height:26px; object-fit:contain; background:#fff; border-radius:3px;
    cursor:pointer; box-sizing:border-box; border:2px solid transparent; position:relative;
  }}
  .logo-chip:hover {{ outline:2px solid #2a78d6; }}
  .logo-chip.selected {{ border-color:#2a78d6; box-shadow:0 0 0 2px rgba(42,120,214,0.35); }}
  #backBtn {{
    position:absolute; top:14px; left:14px; z-index:5;
    background:#fff; border:1px solid rgba(11,11,11,0.15); border-radius:6px;
    padding:6px 12px; font-size:13px; cursor:pointer; display:none;
    box-shadow:0 1px 4px rgba(0,0,0,0.12);
  }}

  .tooltip {{
    position:absolute; pointer-events:none; background:#141413; color:#fff;
    font-size:12px; line-height:1.5; padding:8px 10px; border-radius:6px;
    max-width:220px; z-index:10; opacity:0; transition:opacity 120ms ease;
    box-shadow:0 4px 12px rgba(0,0,0,0.25);
  }}
  .tooltip .name {{ font-weight:600; margin-bottom:2px; display:flex; align-items:center; gap:6px; }}
  .tooltip .flag {{ width:16px; height:auto; border-radius:2px; box-shadow:0 0 0 1px rgba(255,255,255,0.25); flex-shrink:0; }}
  .tooltip .note {{ color:#b8b6ad; font-size:10.5px; margin-top:3px; }}
  .tooltip .missing {{ color:#fab219; }}

  .basket-bar {{
    position:fixed; left:0; right:0; bottom:0; background:#fff; border-top:1px solid #e1e0d9;
    box-shadow:0 -2px 10px rgba(0,0,0,0.08); padding:12px 20px; display:flex; align-items:center;
    gap:14px; z-index:20; font-size:13px;
  }}
  .basket-chips {{ display:flex; gap:6px; flex:1; overflow-x:auto; min-height:34px; align-items:center; }}
  .basket-chip {{
    display:flex; align-items:center; gap:5px; background:#f4f3ef; border:1px solid #e1e0d9;
    border-radius:16px; padding:3px 8px 3px 3px; flex-shrink:0;
  }}
  .basket-chip img {{ width:22px; height:22px; object-fit:contain; border-radius:50%; background:#fff; }}
  .basket-chip .x {{ cursor:pointer; color:#898781; font-weight:600; padding:0 2px; }}
  .basket-chip .x:hover {{ color:#141413; }}
  .basket-empty {{ color:#898781; font-size:12.5px; }}
  .basket-count {{ font-family: "IBM Plex Mono", ui-monospace, monospace; color:#52514e; white-space:nowrap; }}
  .basket-clear {{ background:none; border:1px solid #e1e0d9; border-radius:6px; padding:6px 10px; cursor:pointer; color:#52514e; white-space:nowrap; }}
  .basket-clear:hover {{ background:#f4f3ef; }}
  .basket-compare {{
    background:#2a78d6; color:#fff; border:none; border-radius:6px; padding:8px 16px;
    font-weight:600; cursor:pointer; white-space:nowrap;
  }}
  .basket-compare:disabled {{ background:#c3c2b7; cursor:not-allowed; }}
  .cap-note {{ color:#b8790f; font-size:11.5px; white-space:nowrap; }}

  .modal-backdrop {{
    position:fixed; inset:0; background:rgba(11,11,11,0.45); display:none;
    align-items:flex-start; justify-content:center; z-index:30; padding:40px 16px;
    overflow-y:auto;
  }}
  .modal-backdrop.open {{ display:flex; }}
  .modal {{
    background:#fff; border-radius:12px; max-width:720px; width:100%;
    box-shadow:0 12px 40px rgba(0,0,0,0.25); padding:22px 26px 18px;
  }}
  .modal-head {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px; }}
  .modal h2 {{ font-size:17px; margin:0 0 2px; }}
  .modal .subtext {{ font-size:12.5px; color:#52514e; margin:0 0 14px; line-height:1.5; }}
  .modal-close {{ background:none; border:none; font-size:20px; cursor:pointer; color:#898781; line-height:1; padding:2px 4px; }}
  .modal-close:hover {{ color:#141413; }}

  .selected-banks-row {{ display:flex; flex-wrap:wrap; gap:5px; margin-bottom:16px; }}
  .selected-bank-pill {{
    font-size:11.5px; background:#f4f3ef; border:1px solid #e1e0d9; border-radius:12px;
    padding:3px 9px; color:#52514e;
  }}

  .concept-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px 22px; max-height:52vh; overflow-y:auto; padding-right:4px; }}
  .concept-category {{ border:1px solid #e1e0d9; border-radius:8px; padding:10px 12px; }}
  .concept-cat-head {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }}
  .cat-name {{ font-size:12.5px; font-weight:600; text-transform:uppercase; letter-spacing:0.03em; color:#52514e; }}
  .cat-toggle {{
    font-size:11px; background:none; border:1px solid #e1e0d9; border-radius:5px;
    padding:2px 7px; cursor:pointer; color:#2a78d6;
  }}
  .cat-toggle:hover {{ background:#f4f3ef; }}
  .concept-row {{ display:flex; align-items:center; gap:7px; font-size:13px; padding:3px 0; cursor:pointer; }}
  .concept-row input {{ cursor:pointer; }}

  .modal-footer {{ display:flex; justify-content:space-between; align-items:center; margin-top:16px; padding-top:14px; border-top:1px solid #e1e0d9; }}
  .concept-count {{ font-family:"IBM Plex Mono", ui-monospace, monospace; font-size:12.5px; color:#52514e; }}
  .continue-btn {{
    background:#2a78d6; color:#fff; border:none; border-radius:6px; padding:9px 18px;
    font-weight:600; cursor:pointer;
  }}
  .continue-btn:disabled {{ background:#c3c2b7; cursor:not-allowed; }}

  .results-modal {{ max-width:min(94vw, 1100px); }}
  .results-sub {{ display:flex; gap:8px; margin-bottom:14px; }}
  .results-sub button {{
    font-size:12.5px; background:none; border:1px solid #e1e0d9; border-radius:6px;
    padding:6px 12px; cursor:pointer; color:#52514e;
  }}
  .results-sub button:hover {{ background:#f4f3ef; }}
  .results-sub .csv-btn {{ color:#2a78d6; border-color:#bcd6f2; margin-left:auto; }}
  .results-table-wrap {{ max-height:60vh; overflow:auto; border:1px solid #e1e0d9; border-radius:8px; }}
  table.results-table {{ border-collapse:collapse; width:100%; font-size:12.5px; }}
  .results-table th, .results-table td {{ padding:7px 12px; text-align:center; white-space:nowrap; border-bottom:1px solid #eeede7; }}
  .results-table th:first-child, .results-table td:first-child {{ text-align:left; position:sticky; left:0; background:#fff; z-index:2; }}
  .results-table thead th {{ position:sticky; top:0; background:#fafaf7; z-index:1; font-weight:600; border-bottom:1px solid #e1e0d9; }}
  .results-table thead th:first-child {{ z-index:3; }}
  .results-table .bank-col-head {{ display:flex; flex-direction:column; align-items:center; gap:3px; max-width:120px; }}
  .results-table .bank-col-head img {{ height:22px; width:auto; max-width:70px; object-fit:contain; }}
  .results-table .bank-col-head span {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:120px; cursor:help; }}
  .results-table .metric-name {{ color:#141413; }}
  .results-table td.best {{ color:#1f7a4d; font-weight:700; background:#f1faf4; }}
  .results-table td.miss {{ color:#c3c2b7; cursor:help; }}
  .results-table td.disagree {{ color:#8a5a00; cursor:help; background:#fff8ec; border-bottom:1px dashed #d9a441; }}
  .results-footnote {{ font-size:11px; color:#898781; margin-top:10px; line-height:1.5; }}
</style></head>
<body>
<div class="page">
  <div class="map-wrap" id="mapWrap">
    <button id="backBtn">&larr; Back to Europe</button>
    <svg viewBox="0 0 680 520"><g id="zoomGroup">
    {inner_svg}
    </g></svg>
    <div id="overlay">
    {''.join(clusters_html)}
    </div>
    <div class="tooltip" id="tooltip"></div>
  </div>
</div>

<div class="basket-bar">
  <div class="basket-chips" id="basketChips"><span class="basket-empty">Click a bank's logo to add it here (up to 6)</span></div>
  <span class="cap-note" id="capNote" style="display:none;">max 6 reached</span>
  <span class="basket-count" id="basketCount"></span>
  <button class="basket-clear" id="clearBtn">Clear all</button>
  <button class="basket-compare" id="compareBtn" disabled>Compare &rarr;</button>
</div>

<div class="modal-backdrop" id="conceptModalBackdrop">
  <div class="modal">
    <div class="modal-head">
      <div>
        <h2>Choose what to compare</h2>
        <p class="subtext">Pick any metrics across these categories, all for FY2025 / 2025-12-31. Most have strong coverage (at least 26 of the 28 banks); coverage is called out next to the few that don't.</p>
      </div>
      <button class="modal-close" id="modalCloseBtn">&times;</button>
    </div>
    <div class="selected-banks-row" id="selectedBanksRow"></div>
    <div class="concept-grid">
      {CONCEPT_CATEGORIES_HTML}
    </div>
    <div class="modal-footer">
      <span class="concept-count" id="conceptCount">0 metrics selected</span>
      <button class="continue-btn" id="continueBtn" disabled>See results &rarr;</button>
    </div>
  </div>
</div>

<div class="modal-backdrop" id="resultsModalBackdrop">
  <div class="modal results-modal">
    <div class="modal-head">
      <div>
        <h2>Comparison</h2>
        <p class="subtext">FY2025 / 2025-12-31. A dash means this bank doesn't report this metric this way for this period - hover it for why. An amber cell means more than one source reports this figure and they genuinely disagree - hover it to see every value and its source.</p>
      </div>
      <button class="modal-close" id="resultsCloseBtn">&times;</button>
    </div>
    <div class="results-sub">
      <button type="button" id="editSelectionBtn">&larr; edit selection</button>
      <button type="button" class="csv-btn" id="csvBtn">Download CSV</button>
    </div>
    <div class="results-table-wrap">
      <table class="results-table" id="resultsTable"></table>
    </div>
    <div class="results-footnote" id="resultsFootnote"></div>
  </div>
</div>

<script>
const BANK_DATA = {json.dumps(bank_data)};
const CENTROIDS = {json.dumps(clusters_json)};
const PAGE_SCALE = {PAGE_SCALE};
const VB_CX = 340, VB_CY = 260;
const MAX_BASKET = 6;
let state = {{ k: 1, tx: 0, ty: 0 }};
let selected = [];

function project(cx, cy) {{
  return {{ x: (state.tx + state.k * cx) * PAGE_SCALE, y: (state.ty + state.k * cy) * PAGE_SCALE }};
}}

function layoutClusters() {{
  for (const code in CENTROIDS) {{
    const el = document.getElementById('cl-' + code);
    if (!el) continue;
    const c = CENTROIDS[code];
    // at overview zoom, use the cluster's (possibly decluttered) visual anchor; once
    // zoomed into a country, snap to its real geographic centroid - the override only
    // exists to fix overview-level crowding, not to misplace a zoomed-in view.
    const useReal = state.k > 1;
    const p = project(useReal ? c.cx : c.acx, useReal ? c.cy : c.acy);
    el.style.left = p.x + 'px';
    el.style.top = p.y + 'px';
  }}
}}

function applyZoom(k, tx, ty) {{
  state = {{ k, tx, ty }};
  document.getElementById('zoomGroup').style.transform = `translate(${{tx}}px, ${{ty}}px) scale(${{k}})`;
  document.querySelectorAll('.cluster').forEach(c => c.style.opacity = 0);
  setTimeout(() => {{
    layoutClusters();
    document.querySelectorAll('.cluster').forEach(c => c.style.opacity = 1);
  }}, 480);
  document.getElementById('backBtn').style.display = (k === 1) ? 'none' : 'block';
}}

function zoomToCountry(code) {{
  const c = CENTROIDS[code];
  if (!c) return;
  const k = 3.1;
  const tx = VB_CX - k * c.cx;
  const ty = VB_CY - k * c.cy;
  applyZoom(k, tx, ty);
}}

// ---- tooltip ----
const tooltip = document.getElementById('tooltip');
function flagImg(d) {{
  if (!d.flag_data_uri) return '';
  return `<img class="flag" src="${{d.flag_data_uri}}" alt="${{d.country}}">`;
}}
function fmtAssets(d) {{
  if (d.total_assets_eur_bn == null) {{
    return '<div class="missing">Total assets: missing from source (FY2025)</div>';
  }}
  let html = `<div>Total assets (FY2025): <b>&euro;${{d.total_assets_eur_bn.toFixed(1)}}bn</b></div>`;
  if (d.currency_note) html += `<div class="note">${{d.currency_note}}</div>`;
  return html;
}}
document.querySelectorAll('.logo-chip').forEach(img => {{
  img.addEventListener('mouseenter', () => {{
    const d = BANK_DATA[img.dataset.lei];
    tooltip.innerHTML = `<div class="name">${{flagImg(d)}}<span>${{d.name}}</span></div>${{fmtAssets(d)}}`;
    tooltip.style.opacity = 1;
  }});
  img.addEventListener('mousemove', (e) => {{
    const wrapRect = document.getElementById('mapWrap').getBoundingClientRect();
    let x = e.clientX - wrapRect.left + 14;
    let y = e.clientY - wrapRect.top + 14;
    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
  }});
  img.addEventListener('mouseleave', () => {{ tooltip.style.opacity = 0; }});
}});

// ---- basket ----
function renderBasket() {{
  const chipsEl = document.getElementById('basketChips');
  const countEl = document.getElementById('basketCount');
  const compareBtn = document.getElementById('compareBtn');
  const capNote = document.getElementById('capNote');
  if (selected.length === 0) {{
    chipsEl.innerHTML = '<span class="basket-empty">Click a bank\\'s logo to add it here (up to 6)</span>';
  }} else {{
    chipsEl.innerHTML = selected.map(lei => {{
      const d = BANK_DATA[lei];
      const img = document.querySelector(`.logo-chip[data-lei="${{lei}}"]`);
      const src = img ? img.src : '';
      return `<span class="basket-chip" data-lei="${{lei}}"><img src="${{src}}"><span>${{d.name}}</span><span class="x" data-remove="${{lei}}">&times;</span></span>`;
    }}).join('');
  }}
  countEl.textContent = selected.length + ' / ' + MAX_BASKET + ' selected';
  compareBtn.disabled = selected.length === 0;
  capNote.style.display = selected.length >= MAX_BASKET ? 'inline' : 'none';

  chipsEl.querySelectorAll('[data-remove]').forEach(x => {{
    x.addEventListener('click', () => toggleSelect(x.dataset.remove));
  }});
}}

function toggleSelect(lei) {{
  const img = document.querySelector(`.logo-chip[data-lei="${{lei}}"]`);
  const idx = selected.indexOf(lei);
  if (idx >= 0) {{
    selected.splice(idx, 1);
    if (img) img.classList.remove('selected');
  }} else {{
    if (selected.length >= MAX_BASKET) {{
      const capNote = document.getElementById('capNote');
      capNote.style.display = 'inline';
      capNote.style.color = '#c0392b';
      setTimeout(() => {{ capNote.style.color = ''; }}, 600);
      return;
    }}
    selected.push(lei);
    if (img) img.classList.add('selected');
  }}
  renderBasket();
}}

document.querySelectorAll('.logo-chip').forEach(img => {{
  img.addEventListener('click', (e) => {{
    e.stopPropagation();
    toggleSelect(img.dataset.lei);
  }});
}});
document.getElementById('clearBtn').addEventListener('click', () => {{
  selected.forEach(lei => {{
    const img = document.querySelector(`.logo-chip[data-lei="${{lei}}"]`);
    if (img) img.classList.remove('selected');
  }});
  selected = [];
  renderBasket();
}});
// ---- concept picker modal ----
const CONCEPT_LABELS = {json.dumps(CONCEPT_LABELS)};
const COMPARISON_DATA = {json.dumps(COMPARISON_DATA)};
const METRIC_DIRECTION = {json.dumps(METRIC_DIRECTION)};
const METRIC_KIND = {json.dumps(METRIC_KIND)};
const DERIVED_RATIO = {json.dumps(DERIVED_RATIO)};
const modalBackdrop = document.getElementById('conceptModalBackdrop');

function renderSelectedBanksRow() {{
  const row = document.getElementById('selectedBanksRow');
  row.innerHTML = selected.map(lei => `<span class="selected-bank-pill">${{BANK_DATA[lei].name}}</span>`).join('');
}}

function updateConceptCount() {{
  const checked = document.querySelectorAll('.concept-check:checked');
  document.getElementById('conceptCount').textContent = checked.length + ' metric' + (checked.length === 1 ? '' : 's') + ' selected';
  document.getElementById('continueBtn').disabled = checked.length === 0;
}}

document.getElementById('compareBtn').addEventListener('click', () => {{
  if (selected.length === 0) return;
  renderSelectedBanksRow();
  modalBackdrop.classList.add('open');
}});
document.getElementById('modalCloseBtn').addEventListener('click', () => modalBackdrop.classList.remove('open'));
modalBackdrop.addEventListener('click', (e) => {{ if (e.target === modalBackdrop) modalBackdrop.classList.remove('open'); }});

document.querySelectorAll('.concept-check').forEach(cb => cb.addEventListener('change', updateConceptCount));

document.querySelectorAll('.cat-toggle').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const ids = btn.dataset.ids.split(',');
    const boxes = ids.map(id => document.querySelector(`.concept-check[value="${{id}}"]`));
    const allChecked = boxes.every(b => b.checked);
    boxes.forEach(b => {{ b.checked = !allChecked; }});
    btn.textContent = allChecked ? 'select all' : 'clear';
    updateConceptCount();
  }});
}});

// ---- results view ----
const resultsBackdrop = document.getElementById('resultsModalBackdrop');
let lastChosenConcepts = [];

function fmtOne(kind, v) {{
  if (kind === 'ratio') return (v * 100).toFixed(1) + '%';
  return Math.abs(v) >= 1000
    ? '€' + (v / 1000).toLocaleString('en-US', {{minimumFractionDigits:1, maximumFractionDigits:1}}) + 'bn'
    : '€' + Math.round(v).toLocaleString('en-US') + 'm';
}}

function fmtValue(concept, cell) {{
  if (!cell || cell.status !== 'ok') return null;
  const kind = METRIC_KIND[concept];
  if (cell.disagreement) {{
    return cell.disagreement.values.map(v => fmtOne(kind, v.value)).join(' / ');
  }}
  return fmtOne(kind, cell.value);
}}

function getCell(lei, concept) {{
  const bankData = COMPARISON_DATA[lei] || {{}};
  const spec = DERIVED_RATIO[concept];
  if (!spec) return bankData[concept];
  const [baseConcept, denomConcept] = spec;
  const baseCell = bankData[baseConcept];
  if (!baseCell || baseCell.status !== 'ok') {{
    return {{status: 'missing', reason: (baseCell && baseCell.reason) || (CONCEPT_LABELS[baseConcept] + ' is not available for this bank/period.')}};
  }}
  const denomCell = bankData[denomConcept];
  if (!denomCell || denomCell.status !== 'ok' || !denomCell.value) {{
    return {{status: 'missing', reason: CONCEPT_LABELS[denomConcept] + ' not available for this bank/period, so this ratio cannot be computed.'}};
  }}
  return {{status: 'ok', value: baseCell.value / denomCell.value}};
}}

function renderResultsTable(leis, concepts) {{
  const table = document.getElementById('resultsTable');
  const thead = '<thead><tr><th>Metric</th>' + leis.map(lei => {{
    const d = BANK_DATA[lei];
    const img = document.querySelector(`.logo-chip[data-lei="${{lei}}"]`);
    const src = img ? img.src : '';
    return `<th><div class="bank-col-head"><img src="${{src}}"><span title="${{d.name}}">${{d.name}}</span></div></th>`;
  }}).join('') + '</tr></thead>';

  const bodyRows = concepts.map(concept => {{
    const cells = leis.map(lei => getCell(lei, concept));
    const direction = METRIC_DIRECTION[concept];
    let bestIdx = -1;
    // Disagreement cells are excluded from "best" comparison - when the sources
    // themselves disagree, there's no single number to rank against the others.
    const okIdx = cells.map((c, i) => (c && c.status === 'ok' && !c.disagreement) ? i : -1).filter(i => i >= 0);
    if (direction && okIdx.length >= 2) {{
      bestIdx = okIdx.reduce((best, i) => {{
        const v = cells[i].value, bv = cells[best].value;
        return (direction === 'up' ? v > bv : v < bv) ? i : best;
      }}, okIdx[0]);
    }}
    const tds = cells.map((cell, i) => {{
      const val = fmtValue(concept, cell);
      if (val === null) {{
        const reason = (cell && cell.reason) ? cell.reason : 'Not available for this bank/period.';
        return `<td class="miss" title="${{reason.replace(/"/g, '&quot;')}}">—</td>`;
      }}
      if (cell.disagreement) {{
        const labels = cell.disagreement.values.map(v => v.label).join(' vs. ');
        const title = `${{labels}} - ${{cell.disagreement.note}}`.replace(/"/g, '&quot;');
        return `<td class="disagree" title="${{title}}">${{val}}</td>`;
      }}
      return `<td class="${{i === bestIdx ? 'best' : ''}}">${{val}}</td>`;
    }}).join('');
    return `<tr><td class="metric-name">${{CONCEPT_LABELS[concept]}}</td>${{tds}}</tr>`;
  }}).join('');

  table.innerHTML = thead + '<tbody>' + bodyRows + '</tbody>';

  const nonEur = leis.some(lei => (BANK_DATA[lei] || {{}}).currency_note);
  document.getElementById('resultsFootnote').textContent = nonEur
    ? 'Amounts converted to EUR using ECB reference rates (2026-10-28) for banks reporting in DKK/NOK/SEK. Ratios need no conversion.'
    : '';
}}

function timestampSuffix() {{
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${{d.getFullYear()}}-${{pad(d.getMonth() + 1)}}-${{pad(d.getDate())}}_${{pad(d.getHours())}}${{pad(d.getMinutes())}}${{pad(d.getSeconds())}}`;
}}

function exportCSV(leis, concepts) {{
  const header = ['Metric', ...leis.map(lei => BANK_DATA[lei].name)];
  const lines = [header];
  concepts.forEach(concept => {{
    const row = [CONCEPT_LABELS[concept]];
    leis.forEach(lei => {{
      const cell = getCell(lei, concept);
      const val = fmtValue(concept, cell);
      row.push(val === null ? 'n/a' : val);
    }});
    lines.push(row);
  }});
  const csv = lines.map(r => r.map(c => `"${{String(c).replace(/"/g, '""')}}"`).join(',')).join('\\r\\n');
  const blob = new Blob(['\\ufeff' + csv], {{type: 'text/csv;charset=utf-8;'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `bank_comparison_${{timestampSuffix()}}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}}

document.getElementById('continueBtn').addEventListener('click', () => {{
  const chosenConcepts = [...document.querySelectorAll('.concept-check:checked')].map(cb => cb.value);
  lastChosenConcepts = chosenConcepts;
  modalBackdrop.classList.remove('open');
  renderResultsTable(selected, chosenConcepts);
  resultsBackdrop.classList.add('open');
}});
document.getElementById('resultsCloseBtn').addEventListener('click', () => resultsBackdrop.classList.remove('open'));
resultsBackdrop.addEventListener('click', (e) => {{ if (e.target === resultsBackdrop) resultsBackdrop.classList.remove('open'); }});
document.getElementById('editSelectionBtn').addEventListener('click', () => {{
  resultsBackdrop.classList.remove('open');
  renderSelectedBanksRow();
  modalBackdrop.classList.add('open');
}});
document.getElementById('csvBtn').addEventListener('click', () => exportCSV(selected, lastChosenConcepts));

document.querySelectorAll('.cluster').forEach(el => {{
  el.addEventListener('click', () => zoomToCountry(el.dataset.code));
}});
document.querySelectorAll('path[id]').forEach(el => {{
  if (CENTROIDS[el.id]) el.addEventListener('click', () => zoomToCountry(el.id));
}});
document.getElementById('backBtn').addEventListener('click', () => applyZoom(1, 0, 0));

layoutClusters();
renderBasket();
</script>
</body></html>
"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT, "| banks:", len(bank_data), "| countries:", len(clusters_json))
