"""Playwright-driven scraper for the Pillar 3 Data Hub, used because EBA has not (yet)
responded about a bulk/API channel (see DATA_SOURCES_NOTES.md, "Update 2026-09-19").

Why Playwright and not a simpler HTTP client: EDAP's "Data Points Report" renders as a
Microsoft Power BI report embedded via a cross-origin iframe (app.powerbi.com/reportEmbed).
That means the filter controls (Entity / Module / Reference Date / Template) live inside a
DOM this session's own in-chat browser tooling could NOT see at all - `read_page` and
`find()` both came back empty on that iframe, confirmed by direct inspection on 2026-09-19.
Playwright doesn't have that limitation: it drives the browser over the DevTools Protocol,
so `page.frame_locator(...)` can reach into a cross-origin iframe's DOM just fine. That's the
whole reason this has to be a real local Playwright script rather than something built from
inside this session - it needs a browser Chrome DevTools Protocol can attach to and reach
the internet, neither of which this sandboxed session has (its own network egress is
allowlisted and blocked app.powerbi.com/edap-public.eba.europa.eu when tested).

Two different DOM "layers" are involved:
  - The four filter dropdowns are Power BI slicers *inside* the cross-origin iframe. I could
    not inspect their actual markup from this session (network-blocked here, DOM-blind in
    the chat browser), so SLICER_SELECTORS below encodes the *standard* Power BI
    dropdown-slicer pattern (a `role="listbox"` trigger opening a `role="option"` popup) as a
    starting point, not a verified one.
  - The "Export data" control is part of EDAP's OWN page chrome (`#exportFileButton`), same
    origin as edap-public.eba.europa.eu itself - I confirmed this element exists via direct
    DOM inspection on the "Official Data and Templates Visualisation" report, and the
    reportTemplate.js it comes from is shared across every /Report/index/* page, so it
    should be present here too.

BEFORE trusting this end to end: run
    playwright codegen https://edap-public.eba.europa.eu/Report/index/MTE2
locally, manually set the four filters and trigger an export while it's recording, and swap
whatever selectors it captures into SLICER_SELECTORS / EXPORT_SELECTORS below. Treat this
file as a strong starting skeleton, not a verified working scraper - Power BI's internal
markup is not a stable public contract and this is the one part of the pipeline most likely
to need hand-fixing on first run.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PWTimeoutError, sync_playwright

DATA_POINTS_REPORT_URL = "https://edap-public.eba.europa.eu/Report/index/MTE2"
POWERBI_IFRAME_SELECTOR = 'iframe[src*="powerbi.com"]'

# Best-effort standard Power BI dropdown-slicer pattern - UNVERIFIED against this specific
# report. Adjust after a `playwright codegen` pass (see module docstring).
SLICER_SELECTORS = {
    "field_container": 'div[aria-label="{field}"]',
    "dropdown_trigger": 'div[aria-label="{field}"] .slicer-dropdown-menu, div[aria-label="{field}"] [role="button"]',
    "search_box": '.slicer-dropdown-popup input[type="text"], .searchInput',
    "option": '.slicer-dropdown-popup [role="option"]:has-text("{value}"), [role="listbox"] [role="option"]:has-text("{value}")',
}

# The export trigger lives in EDAP's own page chrome (same-origin), confirmed present in the
# DOM on 2026-09-19 - see DATA_SOURCES_NOTES.md.
EXPORT_BUTTON_SELECTOR = "#exportFileButton, #exportFileButtonContainer"
EXPORT_MENU_OPTION_SELECTOR = 'text="Export data"'  # Power BI's own submenu item; adjust if EDAP wraps it differently


@dataclass(frozen=True)
class DataPointQuery:
    entity: str
    module: str
    reference_date: str
    template: str


def _select_slicer(page: Page, field: str, value: str, timeout_ms: int = 15000) -> None:
    frame = page.frame_locator(POWERBI_IFRAME_SELECTOR)
    trigger = frame.locator(SLICER_SELECTORS["dropdown_trigger"].format(field=field))
    trigger.click(timeout=timeout_ms)
    search = frame.locator(SLICER_SELECTORS["search_box"])
    if search.count() > 0:
        search.first.fill(value)
    option = frame.locator(SLICER_SELECTORS["option"].format(value=value))
    option.first.click(timeout=timeout_ms)
    page.keyboard.press("Escape")  # close the popup


def export_data_points(query: DataPointQuery, out_dir: Path, headless: bool = True) -> Path:
    """Set the four filters and trigger EDAP's native "Export data", saving the result under
    out_dir. Raises playwright.sync_api.TimeoutError with a specific field name if a selector
    doesn't match - that tells you exactly which slicer's selector needs fixing, rather than
    failing silently."""
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(accept_downloads=True)
        page.goto(DATA_POINTS_REPORT_URL, wait_until="networkidle")
        page.wait_for_selector(POWERBI_IFRAME_SELECTOR, timeout=30000)
        time.sleep(3)  # Power BI's own internal render, not just the iframe's load event

        for field, value in [
            ("Entity", query.entity),
            ("Entity Module", query.module),
            ("Reference Date", query.reference_date),
            ("Template", query.template),
        ]:
            try:
                _select_slicer(page, field, value)
            except PWTimeoutError as exc:
                browser.close()
                raise PWTimeoutError(
                    f"Could not set slicer '{field}' to '{value}' - selector likely needs "
                    f"updating from a `playwright codegen {DATA_POINTS_REPORT_URL}` run. "
                    f"Original error: {exc}"
                ) from exc

        page.click(EXPORT_BUTTON_SELECTOR)
        page.click(EXPORT_MENU_OPTION_SELECTOR)
        with page.expect_download(timeout=30000) as download_info:
            pass  # the click above should already have started the download
        download = download_info.value
        dest = out_dir / f"{query.entity}_{query.module}_{query.reference_date}.xlsx"
        download.save_as(dest)
        browser.close()
        return dest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entity")
    parser.add_argument("module")
    parser.add_argument("reference_date")
    parser.add_argument("template")
    parser.add_argument("--out-dir", default="data/raw/p3dh")
    parser.add_argument("--headed", action="store_true", help="watch it run - recommended for the first attempt")
    args = parser.parse_args()

    result = export_data_points(
        DataPointQuery(args.entity, args.module, args.reference_date, args.template),
        Path(args.out_dir),
        headless=not args.headed,
    )
    print(f"saved to {result}")
