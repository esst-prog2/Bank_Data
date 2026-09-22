"""The Pillar 3 Data Hub publication calendar.

EBA's P3DH Implementing Technical Standards (Article 4) fix how long institutions have,
after a reference date, to submit their disclosures. New data therefore arrives in
predictable "waves" rather than continuously:

    reference date type      submission deadline
    ------------------------ --------------------
    quarterly                reference date + 4 months
    semi-annual               reference date + 4 months
    year-end (annual)         reference date + 6 months
    year-end remuneration     reference date + 8 months

This module turns that calendar into a list of "reference dates we should have started
seeing data for by now", so run_update.py can check for new waves instead of re-downloading
everything on every run. It does NOT know the exact day EBA actually publishes each wave
(that can slip) - it gives you the earliest date a check becomes worthwhile, and you still
need edap_downloader to confirm whether the data is actually there yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from dateutil.relativedelta import relativedelta
from enum import Enum


class ReferenceDateType(str, Enum):
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    YEAR_END = "year_end"
    YEAR_END_REMUNERATION = "year_end_remuneration"


_DEADLINE_MONTHS = {
    ReferenceDateType.QUARTERLY: 4,
    ReferenceDateType.SEMI_ANNUAL: 4,
    ReferenceDateType.YEAR_END: 6,
    ReferenceDateType.YEAR_END_REMUNERATION: 8,
}


@dataclass(frozen=True)
class Wave:
    reference_date: date
    reference_type: ReferenceDateType
    earliest_expected_publication: date

    @property
    def wave_id(self) -> str:
        return f"{self.reference_date.isoformat()}-{self.reference_type.value}"


def _reference_dates_since(start_year: int, today: date) -> list[tuple[date, ReferenceDateType]]:
    """All quarter-end reference dates from start_year through today, each tagged with
    every classification it falls under (a December date is both QUARTERLY and YEAR_END,
    for example, since institutions submit different templates against the same date)."""
    out: list[tuple[date, ReferenceDateType]] = []
    year = start_year
    while True:
        for month in (3, 6, 9, 12):
            d = date(year, month, 30) if month in (6, 9) else date(year, month, 31)
            if d > today:
                return out
            out.append((d, ReferenceDateType.QUARTERLY))
            if month in (6, 12):
                out.append((d, ReferenceDateType.SEMI_ANNUAL))
            if month == 12:
                out.append((d, ReferenceDateType.YEAR_END))
                out.append((d, ReferenceDateType.YEAR_END_REMUNERATION))
        year += 1


def expected_waves(today: date | None = None, start_year: int = 2025) -> list[Wave]:
    """Every wave whose submission deadline has already passed as of `today` - i.e. every
    wave that COULD already be published. P3DH itself only has data from the 2025-06
    reference date onward (it launched Jan 2026), so start_year defaults to 2025.
    """
    today = today or date.today()
    waves = []
    for ref_date, ref_type in _reference_dates_since(start_year, today):
        deadline = ref_date + relativedelta(months=_DEADLINE_MONTHS[ref_type])
        if deadline <= today:
            waves.append(Wave(ref_date, ref_type, deadline))
    return waves


if __name__ == "__main__":
    for w in expected_waves():
        print(w.wave_id, "- expected published by", w.earliest_expected_publication)
