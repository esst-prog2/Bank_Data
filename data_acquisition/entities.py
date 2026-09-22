"""The universe of institutions (identified by LEI) this project tracks.

We deliberately do NOT try to auto-discover "every LEI in P3DH" - see DATA_SOURCES_NOTES.md
for why that's not currently possible without either EBA's cooperation or a lot of fragile
Power BI scraping. This module manages an explicit list in data/entities.csv instead.

Preferred workflow (real, EBA-sourced list): the Transparency Exercise and Stress Test
landing pages list every participating bank with its LEI baked into the result-PDF filename -
use eba_exercises.build_entities_csv() to populate data/entities.csv from one of those
directly, e.g.:
    python -m data_acquisition.eba_exercises transparency 2025

Fallback workflow (when you want a specific bank not in either exercise's population):
    python -m data_acquisition.gleif_client "Some Bank Name"   # find candidate LEIs
    # confirm the right one by hand, then add a row to data/entities.csv
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

_ENTITIES_CSV = Path(__file__).resolve().parent.parent / "data" / "entities.csv"


@dataclass(frozen=True)
class Entity:
    lei: str
    name: str
    country: str
    notes: str = ""


def load_entities(path: Path = _ENTITIES_CSV) -> list[Entity]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found - copy data/entities.csv.example to data/entities.csv "
            "and add at least one bank (see the module docstring for how to find LEIs)."
        )
    with path.open(newline="", encoding="utf-8") as f:
        return [Entity(**row) for row in csv.DictReader(f)]


def validate_against_gleif(entities: list[Entity]) -> list[str]:
    """Returns a list of human-readable problems (empty list = all good). Cheap sanity
    check to run before a big download job - catches typo'd LEIs early."""
    from data_acquisition.gleif_client import GleifError, get_lei_record

    problems = []
    for e in entities:
        try:
            get_lei_record(e.lei)
        except GleifError as exc:
            problems.append(f"{e.name} ({e.lei}): {exc}")
    return problems


if __name__ == "__main__":
    ents = load_entities()
    print(f"{len(ents)} entities loaded")
    issues = validate_against_gleif(ents)
    if issues:
        print("Problems found:")
        for p in issues:
            print(" -", p)
    else:
        print("All LEIs validate against GLEIF.")
