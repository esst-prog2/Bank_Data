"""The one module you should have to change once EBA's actual bulk-access mechanism is known.

Everything else in this package (waves, entities, run_update) is written against this
module's interface, not against any specific EBA implementation detail - so when you get an
answer from P3DH@eba.europa.eu (see DATA_SOURCES_NOTES.md), or find/confirm a real endpoint,
the fix is localized to `fetch_module()` below.

**2026-10-06: Option B (Playwright) is now real, not a stub.** `edap_scraper.py` was
verified end to end against the live page (see its own docstring and
DATA_SOURCES_NOTES.md's 2026-10-06 entry) - real filter selection, real navigation, real
"Export data" click, real downloaded file, for a real bank (Erste Group Bank AG) and a real
template (EU KM1). `fetch_module()` below now calls it directly rather than raising. No
official bulk/API channel has been confirmed by EBA (Option A), so this is the only
implemented path.

**Naming note kept for compatibility:** this function is still called `fetch_module()` and
still takes a `module` parameter, matching `run_update.py`'s existing per-(entity, wave,
module) loop - but P3DH's own UI doesn't actually need a Module filter at all
(`edap_scraper.py`'s investigation found Module is fully cross-filtered from Template, and
confirmed a live export with Module left unset produces the same data). So here, `module`
is treated as the exact P3DH **Template** option text (e.g. "K_61.00 - EU KM1 - Key metrics
template"), not a short code like "CODIS" - the parameter is not renamed yet to avoid
touching `run_update.py`'s loop and `data/modules.txt` convention in the same change as the
scraper wiring; see DATA_SOURCES_NOTES.md for the full reasoning and PLANNING_LOG.md for the
decision to defer the rename.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


class BulkAccessNotConfirmed(NotImplementedError):
    """No longer raised by the default path - kept for callers that still catch it
    specifically, and for the (still real) case where a caller passes an entity LEI this
    project doesn't track, where there's no display name to resolve against P3DH."""


@dataclass(frozen=True)
class DownloadResult:
    lei: str
    reference_date: date
    module: str
    file_path: Path
    source: str  # "official_bulk" | "manual_export" | "playwright_export"


def fetch_module(lei: str, reference_date: date, module: str, out_dir: Path) -> DownloadResult:
    """Fetch one P3DH template's data points (despite the name - see module docstring) for
    one entity/period, via the verified Playwright scraper.

    `module` here is P3DH's exact Template option text (e.g. "K_61.00 - EU KM1 - Key
    metrics template"), not a short module code - see module docstring for why.
    `reference_date` must be a `datetime.date` matching one of P3DH's own available
    reference dates (currently 2025-06-30 through 2026-06-30 - nothing earlier; see
    `edap_scraper.py`'s docstring) and is formatted here as "DD/MM/YYYY" to match the
    slicer's own display format.

    Raises `BulkAccessNotConfirmed` if `lei` isn't in `data/entities.csv` (no display name
    to resolve against P3DH's name-based Entity filter - see `edap_scraper.py`'s "Entity is
    selected by display/legal name, not LEI" finding). Raises whatever
    `edap_scraper.export_data_points()` raises (typically `playwright.sync_api.TimeoutError`
    naming the specific slicer that failed) on a genuine scraper/page failure.
    """
    from data_acquisition import edap_scraper
    from data_acquisition.entities import load_entities

    entity = next((e for e in load_entities() if e.lei == lei), None)
    if entity is None or not entity.name:
        raise BulkAccessNotConfirmed(
            f"LEI {lei} not found in data/entities.csv (or has no resolved name) - P3DH's "
            "Entity filter takes a display name, not an LEI, so there's nothing to search "
            "for. Add/resolve it there first (see data_acquisition/gleif_client.py)."
        )

    query = edap_scraper.DataPointQuery(
        entity=entity.name,
        reference_date=reference_date.strftime("%d/%m/%Y"),
        template=module,
    )
    file_path = edap_scraper.export_data_points(query, out_dir, headless=True)
    return DownloadResult(
        lei=lei,
        reference_date=reference_date,
        module=module,
        file_path=file_path,
        source="playwright_export",
    )
