"""ESEF (European Single Electronic Format) financial-statement filings via
filings.xbrl.org's public JSON:API - the concrete starting point AGENTS.md's
"Immediate next steps" #5 names, and previously "not begun yet".

Verified 2026-09-25 by fetching the live API for Erste Group Bank AG (LEI
PQOH26KWDF7CG10L6792): AGENTS.md flagged Austria as not reliably indexed on
filings.xbrl.org (only France/Italy/Spain/Netherlands were confirmed well
covered) - it turns out Austria is indexed too, at least for this filer. That
flag was a guess from documentation, not a direct check; this module is the
direct check.

Scope, deliberately narrow for now:
  - One entity's own filings only (`/api/entities/<lei>/filings`) - there is
    still no confirmed way to ask "everyone reporting in country X" the way
    eba_exercises.py can for EBA's exercises, so this can't drive
    entities.csv the way build_entities_csv() does.
  - Assumes a calendar-year fiscal year (period_end "YYYY-12-31" only) - the
    same assumption task 1.5 already flags for waves.py; extend together if a
    pilot bank turns out to have a non-December year-end.
  - Fetches one filing (one period_end) per call, not a bank's whole history -
    each filing's xBRL-JSON is tens of MB, so reconcile.py only asks for the
    one fiscal year it needs rather than a bank's full filing history.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import requests

_API = "https://filings.xbrl.org/api"
_ROOT = Path(__file__).resolve().parent.parent

# {concept: dims} match requires exactly these keys - anything extra (an axis
# member) marks a dimensional breakdown fact (e.g. equity by component), not
# the reported total this module wants.
_BASE_DIMS = {"concept", "entity", "period", "unit"}


class EsefNotFoundError(RuntimeError):
    """No ESEF filing is indexed for this LEI/period on filings.xbrl.org - the
    source genuinely doesn't have it, not a retrieval failure."""


class EsefDataError(RuntimeError):
    """The filing was found but its data could not be fetched or parsed - a
    genuine retrieval/processing failure, never conflated with "not found"."""


@dataclass(frozen=True)
class EsefFiling:
    lei: str
    period_end: str  # "YYYY-MM-DD"
    json_url: str
    report_url: str


def find_filing(lei: str, period_end: str) -> EsefFiling:
    """Looks up the filing whose attributes.period_end matches exactly. If more
    than one filing shares a period_end (a later, superseding submission),
    takes the most recently added one rather than guessing which is "correct" -
    filings.xbrl.org doesn't mark one as canonical."""
    try:
        resp = requests.get(
            f"{_API}/entities/{lei}/filings",
            headers={"Accept": "application/vnd.api+json"},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise EsefDataError(f"failed to list filings for {lei}: {exc}") from exc

    candidates = [f for f in payload.get("data", []) if f["attributes"].get("period_end") == period_end]
    if not candidates:
        raise EsefNotFoundError(f"no ESEF filing indexed for {lei} at period_end={period_end}")
    candidates.sort(key=lambda f: f["attributes"].get("date_added", ""))
    a = candidates[-1]["attributes"]
    return EsefFiling(
        lei=lei,
        period_end=period_end,
        json_url="https://filings.xbrl.org" + a["json_url"],
        report_url="https://filings.xbrl.org" + a["report_url"],
    )


def fetch_facts(lei: str, period_end: str, cache_dir: Path | None = None) -> dict:
    """Returns the filing's parsed xBRL-JSON ({"documentInfo": ..., "facts": {...}}),
    caching it under data/raw/esef/<lei>/<period_end>/facts.json - each file is tens
    of MB, not worth re-downloading on every call. Raises EsefNotFoundError /
    EsefDataError rather than returning partial data silently."""
    cache_dir = cache_dir or _ROOT / "data" / "raw" / "esef" / lei / period_end
    cache_file = cache_dir / "facts.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise EsefDataError(f"failed to read cached {cache_file}: {exc}") from exc

    filing = find_filing(lei, period_end)
    try:
        resp = requests.get(filing.json_url, timeout=180)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise EsefDataError(f"failed to fetch {filing.json_url}: {exc}") from exc

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(resp.text, encoding="utf-8")
    try:
        return json.loads(resp.text)
    except json.JSONDecodeError as exc:
        raise EsefDataError(f"malformed xBRL-JSON from {filing.json_url}: {exc}") from exc


def get_concept_value(facts: dict, concept: str, period_key: str) -> float | None:
    """Returns the single reported total for `concept` at `period_key` (an XBRL
    instant like "2025-01-01T00:00:00" or duration like
    "2024-01-01T00:00:00/2025-01-01T00:00:00"), skipping any fact tagged with
    an extra dimension (a breakdown, e.g. equity by component) - only the
    undimensioned total counts as "the" reported figure. None if no such total
    fact exists (this filing genuinely doesn't report that concept that way)."""
    for fact in facts.get("facts", {}).values():
        dims = fact.get("dimensions", {})
        if dims.get("concept") != concept or dims.get("period") != period_key:
            continue
        if set(dims) - _BASE_DIMS:
            continue
        return float(fact["value"])
    return None


def fiscal_year_keys(period_end: str) -> tuple[str, str]:
    """(duration_key, instant_key) for the calendar fiscal year ending `period_end`
    ("YYYY-12-31" only - see module docstring's fiscal-year-end assumption)."""
    year = int(period_end[:4])
    if period_end[5:] != "12-31":
        raise ValueError(f"only calendar (Dec 31) fiscal year-ends are supported, got {period_end!r}")
    start = f"{year}-01-01T00:00:00"
    end = f"{year + 1}-01-01T00:00:00"
    return f"{start}/{end}", end
