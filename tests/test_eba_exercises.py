"""Regression tests for two homework 6 findings in eba_exercises.py.

Review 3: build_entities_csv() used to hardcode a 4-column fieldnames list, which
would raise ValueError the moment it ran again against the real entities.csv
(schema grew to 6 columns - sp50_2026_rank, pilot_added - after this function was
first written, and csv.DictWriter's default extrasaction='raise' does not tolerate
a row dict carrying keys outside fieldnames).

Review 7: discover_full_database_files() used to return [] silently when neither
live scraping nor the hardcoded fallback found anything - indistinguishable from a
real empty result, except there is no such thing for this data (every real
exercise/year has full-database files)."""
from __future__ import annotations

import csv

import pytest

from data_acquisition import eba_exercises


def test_build_entities_csv_preserves_existing_schema_and_does_not_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(eba_exercises, "discover_participants", lambda exercise, year: [])

    out_path = tmp_path / "entities.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["lei", "name", "country", "sp50_2026_rank", "pilot_added", "notes"]
        )
        writer.writeheader()
        writer.writerow({
            "lei": "PQOH26KWDF7CG10L6792", "name": "Erste Group Bank AG", "country": "AT",
            "sp50_2026_rank": "1", "pilot_added": "", "notes": "",
        })

    eba_exercises.build_entities_csv("transparency", 2025, out_path=out_path)

    with out_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["sp50_2026_rank"] == "1"
    assert rows[0]["lei"] == "PQOH26KWDF7CG10L6792"


def test_discover_full_database_files_raises_when_nothing_found(monkeypatch):
    monkeypatch.setitem(eba_exercises.EXERCISES, "transparency", {1999: "https://example.invalid/1999"})
    monkeypatch.setattr(
        eba_exercises, "_get_html",
        lambda url: (_ for _ in ()).throw(eba_exercises.requests.RequestException("boom")),
    )
    monkeypatch.setitem(eba_exercises._KNOWN_FULL_DATABASE_FILES, ("transparency", 1999), [])

    with pytest.raises(eba_exercises.ExerciseDataUnavailable):
        eba_exercises.discover_full_database_files("transparency", 1999)
