"""Thin wrapper around the public GLEIF API (https://api.gleif.org).

No API key required. Use this to validate an LEI you already have and to pull the legal
name/country/status for it - NOT to discover which banks are in Pillar 3 scope (GLEIF covers
every LEI-holding entity worldwide, most of which have nothing to do with EBA reporting).

Docs: https://www.gleif.org/en/lei-data/gleif-api
"""

from __future__ import annotations

import requests

_BASE = "https://api.gleif.org/api/v1"


class GleifError(RuntimeError):
    pass


def get_lei_record(lei: str) -> dict:
    """Fetch the full LEI record. Raises GleifError if the LEI doesn't exist."""
    resp = requests.get(f"{_BASE}/lei-records/{lei}", timeout=30)
    if resp.status_code == 404:
        raise GleifError(f"LEI {lei} not found in GLEIF")
    resp.raise_for_status()
    return resp.json()["data"]


def search_by_name(name: str, country: str | None = None, limit: int = 10) -> list[dict]:
    """Search GLEIF by (fuzzy) legal name. Useful for turning "Deutsche Bank AG" into a
    candidate LEI you can then confirm by hand and add to entities.csv - do not trust a
    single top match blindly, legal-name search is fuzzy and banking groups have many
    legal entities."""
    params = {"filter[entity.legalName]": name, "page[size]": limit}
    if country:
        params["filter[entity.legalAddress.country]"] = country
    resp = requests.get(f"{_BASE}/lei-records", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]


def summarize(record: dict) -> dict:
    entity = record["attributes"]["entity"]
    return {
        "lei": record["attributes"]["lei"],
        "legal_name": entity["legalName"]["name"],
        "country": entity["legalAddress"]["country"],
        "status": entity.get("status"),
        "registration_status": record["attributes"]["registration"]["status"],
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: python -m data_acquisition.gleif_client <LEI-or-name>")
        sys.exit(1)
    query = sys.argv[1]
    if len(query) == 20 and query.isalnum():
        print(summarize(get_lei_record(query)))
    else:
        for rec in search_by_name(query):
            print(summarize(rec))
