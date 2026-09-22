"""The one module you should have to change once EBA's actual bulk-access mechanism is known.

Everything else in this package (waves, entities, run_update) is written against this
module's interface, not against any specific EBA implementation detail - so when you get an
answer from P3DH@eba.europa.eu (see DATA_SOURCES_NOTES.md), or find/confirm a real endpoint,
the fix is localized to `fetch_module()` below.

Current state (2026-09-17): no public bulk API is documented or was found by inspecting the
live portal (https://edap-public.eba.europa.eu). The Pillar 3 Data Hub is served as embedded
Power BI reports under an anonymous "Public Access" role; the only in-page download mechanism
is Power BI's own per-visual "Export data" button, which is UI-driven and capped in row count
- not suitable for scripted bulk retrieval. `fetch_module()` therefore raises
NotImplementedError by default so the pipeline fails loudly instead of silently producing
nothing, and documents the two real options below.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


class BulkAccessNotConfirmed(NotImplementedError):
    """Raised until one of the two paths below has actually been wired up and tested."""


@dataclass(frozen=True)
class DownloadResult:
    lei: str
    reference_date: date
    module: str
    file_path: Path
    source: str  # "official_bulk" | "manual_export" | "playwright_export"


def fetch_module(lei: str, reference_date: date, module: str, out_dir: Path) -> DownloadResult:
    """Fetch one disclosure module (e.g. "CODIS", "FINDIS") for one entity/period.

    Option A - official bulk channel (preferred, not yet confirmed to exist):
        If/when EBA (P3DH@eba.europa.eu) provides a documented bulk endpoint or file drop,
        implement the real HTTP call here and return source="official_bulk".

    Option B - Playwright-driven export (fallback, unverified end-to-end):
        Drive a real Chromium session to https://edap-public.eba.europa.eu/Report/index/MTE6,
        set the Entity/Module/Reference Date filters in the "Data Points Report" Power BI
        visual, and trigger its native Export-data button, then move the downloaded file
        here. This uses only a documented UI feature (not an internal API), so it's more
        durable than reverse-engineered endpoints, but it is still one export per
        entity/module/period - budget real wall-clock time for a full run, and expect to
        babysit selectors since Power BI's DOM is not a stable public contract.

    Until one of those is implemented, this raises so run_update.py's failures are visible
    (recorded in the state file) rather than pretending to succeed.
    """
    raise BulkAccessNotConfirmed(
        "No confirmed download path yet - see DATA_SOURCES_NOTES.md. "
        "Email P3DH@eba.europa.eu, or implement the Playwright fallback described in "
        "this function's docstring, then remove this guard."
    )
