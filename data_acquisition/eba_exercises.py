"""EBA's two OTHER public bulk-data programmes: the (now discontinued) EU-wide
Transparency Exercise and the (ongoing, biennial) EU-wide Stress Test.

Unlike the Pillar 3 Data Hub (see edap_downloader.py), both of these are real, confirmed,
directly-downloadable bulk datasets - verified 2026-09-17 by fetching the live landing pages
and following the actual links, not by guessing a URL pattern. Each exercise year's landing
page links to:

  - a handful of "full database" CSV files (bank x template x row of reported values, LEI
    tagged) plus an Excel data dictionary/metadata file
  - one PDF per participating bank, and *the PDF filename itself encodes country + LEI*,
    e.g. "DE_7LTWFZYICNSX8D621K86_TR_2025.pdf" (Transparency) or
    "EBA_ST_DE_7LTWFZYICNSX8D621K86.pdf" (Stress Test) for Deutsche Bank AG.

That second point is a free, authoritative entity list for whichever population of banks was
in scope that year - a much better source for entities.csv than guessing names against GLEIF
(see build_entities_csv() below).

Key differences from Pillar 3, both good and bad:
  - Transparency Exercise: discontinued from June 2025, EBA says data "will no longer be
    updated" - great for historical/reproducible-testing data (matches the README's own v1
    scope), useless for anything going forward.
  - Stress Test: still active but biennial (2023, 2025, next ~2027) and NOT a plain reported
    actual - it's scenario-projected (baseline/adverse) capital and P&L figures. Treat it as
    a distinct, non-comparable series in your reconciliation logic, not a drop-in substitute
    for Pillar 3/ESEF actuals.

Landing-page URLs differ in naming convention year to year (not a guessable pattern), so
EXERCISES below is a maintained registry rather than a formula. Add a year by finding its
landing page (linked from https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/
eu-wide-transparency-exercise or .../eu-wide-stress-testing) and adding one line.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

import requests

_ROOT = Path(__file__).resolve().parent.parent

# Verified landing pages. Add new years here as EBA publishes them.
EXERCISES: dict[str, dict[int, str]] = {
    "transparency": {
        2025: "https://www.eba.europa.eu/eu-wide-transparency-exercise-0",
        2024: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-transparency-exercise/2024-eu-wide-transparency-exercise",
        2023: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-transparency-exercise/2023-eu-wide-transparency-exercise",
        2022: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-transparency-exercise/2022-eu-wide-transparency-exercise",
        2021: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-transparency-exercise/2021-eu-wide-transparency",
        2020: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-transparency-exercise/2020-eu-wide-transparency",
        2019: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-transparency-exercise/2019-eu-wide-transparency",
        2018: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/2018-eu-wide-transparency-exercise",
        2017: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/2017-eu-wide-transparency-exercise",
        2016: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/2016-eu-wide-transparency-exercise",
        2015: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/2015-eu-wide-transparency-exercise",
        2013: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/2013-eu-wide-transparency-exercise",
    },
    "stress_test": {
        2025: "https://www.eba.europa.eu/eu-wide-stress-test-2025",
        2023: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/2025-eu-wide-stress-testing/stress-test-2023",
        2021: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-stress-testing/stress-tests-2021",
        2020: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-stress-testing/eu-wide-stress-testing-2020",
        2018: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-stress-testing/eu-wide-stress-testing-2018",
        2016: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-stress-testing/eu-wide-stress-testing-2016",
        2014: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-stress-testing/eu-wide-stress-testing-2014",
        2011: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-stress-testing/eu-wide-stress-testing-2011",
        2010: "https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-stress-testing/eu-wide-stress-testing-2010",
    },
}

# Confirmed 2026-09-17 for the current year of each exercise - kept as a fallback so the
# module still works even if HTML scraping breaks on an EBA site redesign.
_KNOWN_FULL_DATABASE_FILES = {
    ("transparency", 2025): [
        "https://www.eba.europa.eu/assets/TE2025/Full_database/883401/tr_cre.csv",
        "https://www.eba.europa.eu/assets/TE2025/Full_database/883401/tr_mrk.csv",
        "https://www.eba.europa.eu/assets/TE2025/Full_database/883401/tr_sov.csv",
        "https://www.eba.europa.eu/assets/TE2025/Full_database/883401/tr_oth.csv",
        "https://www.eba.europa.eu/assets/TE2025/Full_database/883401/SDD.xlsx",
        "https://www.eba.europa.eu/assets/TE2025/Full_database/883401/TR_Metadata.xlsx",
    ],
    ("stress_test", 2025): [
        "https://www.eba.europa.eu/assets/st25/full_database/763451/TRA_CRE_IRB.csv",
        "https://www.eba.europa.eu/assets/st25/full_database/763451/TRA_CRE_STA.csv",
        "https://www.eba.europa.eu/assets/st25/full_database/763451/TRA_OTH.csv",
        "https://www.eba.europa.eu/assets/st25/full_database/763451/Data_Dictionary.xlsx",
        "https://www.eba.europa.eu/assets/st25/full_database/763451/Metadata_TR.xlsx",
    ],
}

_FULL_DB_LINK_RE = re.compile(
    r'href="(https://www\.eba\.europa\.eu/assets/[^"]+/[Ff]ull_[Dd]atabase/[^"]+\.(?:csv|xlsx))"',
    re.IGNORECASE,
)
# Matches both "AT_529900S9YO2JHTIIDG38_TR_2025.pdf" (Transparency) and
# "EBA_ST_DE_7LTWFZYICNSX8D621K86.pdf" (Stress Test) style individual-bank result links.
_PARTICIPANT_LINK_RE = re.compile(
    r'href="(https://www\.eba\.europa\.eu/assets/[^"]+/[Bb]ank[s]?_?[Ii]ndividual[s]?_?results/[^"]+\.pdf)"',
    re.IGNORECASE,
)
def _parse_country_and_lei(pdf_url: str) -> tuple[str, str] | None:
    """Filenames look like "AT_529900S9YO2JHTIIDG38_TR_2025.pdf" (Transparency) or
    "EBA_ST_AT_PQOH26KWDF7CG10L6792.pdf" (Stress Test). Split on "_" rather than regex
    word-boundaries, since LEIs are flanked by underscores (a word character), not the
    non-word characters \\b requires - a \\b-based match silently fails here."""
    stem = pdf_url.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    parts = stem.split("_")
    # LEIs are exactly 20 chars and always the longest segment - safe to identify by length
    # alone (unlike a 2-letter country code, which collides with the "TR"/"ST" exercise tags).
    lei = next((p for p in parts if len(p) == 20 and p.isalnum()), None)
    _non_country_tags = {"EBA", "TR", "ST"}
    country = next(
        (p for p in parts if len(p) == 2 and p.isalpha() and p.upper() not in _non_country_tags),
        None,
    )
    if lei and country and country.upper() != "OT" and not set(lei) <= {"X"}:
        # "OT_xxxxxxxxxxxxxxxxxxxx" is EBA's placeholder link for "all other banks" grouped
        # together, not a real institution - skip it rather than record a fake LEI.
        return country.upper(), lei.upper()
    return None


@dataclass(frozen=True)
class Participant:
    country: str
    lei: str
    result_pdf: str
    exercise: str
    year: int


def _get_html(url: str) -> str:
    resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 (research script)"})
    resp.raise_for_status()
    return resp.text


def discover_full_database_files(exercise: str, year: int) -> list[str]:
    """Scrape the landing page for this exercise/year and return every full-database
    CSV/XLSX link found. Falls back to the hardcoded list above if scraping finds nothing
    (e.g. the page structure changed) and a fallback is known for that year."""
    url = EXERCISES[exercise][year]
    try:
        html = _get_html(url)
        links = sorted(set(_FULL_DB_LINK_RE.findall(html)))
        if links:
            return links
    except requests.RequestException:
        pass
    return _KNOWN_FULL_DATABASE_FILES.get((exercise, year), [])


def discover_participants(exercise: str, year: int) -> list[Participant]:
    """Scrape the landing page's per-bank result links to recover the (country, LEI) pairs
    of every institution in scope for that exercise/year - i.e. a real, EBA-sourced entity
    list, rather than a guessed one."""
    url = EXERCISES[exercise][year]
    html = _get_html(url)
    out = []
    for pdf_url in set(_PARTICIPANT_LINK_RE.findall(html)):
        parsed = _parse_country_and_lei(pdf_url)
        if parsed is None:
            continue  # e.g. the "OT_xxxxxxxxxxxxxxxxxxxx" placeholder for unlisted banks
        country, lei = parsed
        out.append(Participant(country, lei, pdf_url, exercise, year))
    return out


def download_full_database(exercise: str, year: int, out_dir: Path | None = None) -> list[Path]:
    out_dir = out_dir or _ROOT / "data" / "raw" / exercise / str(year)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for file_url in discover_full_database_files(exercise, year):
        dest = out_dir / file_url.rsplit("/", 1)[-1]
        try:
            resp = requests.get(
                file_url,
                timeout=120,
                stream=True,
                headers={"User-Agent": "Mozilla/5.0 (research script)"},
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            # EBA's asset server 403s some direct file URLs even with a browser-like
            # User-Agent; skip that file rather than aborting the whole download.
            print(f"skipping {file_url}: {exc}")
            continue
        with dest.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)
        written.append(dest)
    return written


def build_entities_csv(exercise: str, year: int, out_path: Path | None = None) -> Path:
    """Write data/entities.csv from a real exercise's participant list. Names aren't in the
    URL, so the "name" column is left blank for you to fill in (or cross-reference against
    GLEIF with gleif_client.get_lei_record) - the LEI and country are the authoritative part.
    Re-running for a different exercise/year appends new LEIs without duplicating existing
    ones."""
    out_path = out_path or _ROOT / "data" / "entities.csv"
    existing_leis: set[str] = set()
    rows: list[dict] = []
    if out_path.exists():
        with out_path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            existing_leis = {r["lei"] for r in rows}

    for p in discover_participants(exercise, year):
        if p.lei not in existing_leis:
            rows.append({
                "lei": p.lei,
                "name": "",
                "country": p.country,
                "notes": f"discovered via {p.exercise} {p.year}",
            })
            existing_leis.add(p.lei)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["lei", "name", "country", "notes"])
        writer.writeheader()
        writer.writerows(rows)
    return out_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3 or sys.argv[1] not in EXERCISES:
        print("usage: python -m data_acquisition.eba_exercises <transparency|stress_test> <year>")
        sys.exit(1)
    exercise, year = sys.argv[1], int(sys.argv[2])
    files = download_full_database(exercise, year)
    print(f"downloaded {len(files)} files to {files[0].parent if files else '(none found)'}")
    path = build_entities_csv(exercise, year)
    print(f"entities.csv now at {path}")
