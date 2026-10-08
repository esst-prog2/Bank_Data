"""Playwright-driven scraper for the Pillar 3 Data Hub, used because EBA has not (yet)
responded about a bulk/API channel (see DATA_SOURCES_NOTES.md, "Update 2026-09-19").

**Verified against the live page on 2026-10-06** (see DATA_SOURCES_NOTES.md's entry of that
date for the full investigation) - this is no longer the unverified guess it was when first
written. What's confirmed, concretely:

- The four filters are real Power BI slicers inside the cross-origin `app.powerbi.com`
  iframe, each a `div.slicer-dropdown-menu[role="combobox"]`. Their `aria-label`s are the
  INTERNAL field names, which differ from the visible header text for two of the four:
  `ReferenceDate` (header "Ref Date"), `ENT_NAM` (header "Entity Name"), `ModuleName`
  (header "Module Name"), `Template` (header "Template").
- **Entity is selected by display/legal name, not LEI.** Typing a bank's LEI into the
  Entity search box returns zero results; typing "Erste" returns 5 real matches including
  "Erste Group Bank AG". Callers must resolve LEI -> legal name first - `entities.csv`'s
  `name` column (GLEIF-resolved, see the 2026-10-06 entries) is the source for that.
  **Match case-insensitively** - GLEIF's resolved legal names are frequently ALL CAPS
  ("ERSTE GROUP BANK AG") while P3DH displays normal case ("Erste Group Bank AG"); an
  exact-case match falsely reported dozens of real pilot banks (Erste included) as
  "not on P3DH" in a first full-sample run before this was caught and fixed (see
  DATA_SOURCES_NOTES.md's 2026-10-06 entry on the full-pilot-sample run).
- **Module and Template are genuinely different lists, not the same list under two names**
  (this was an open, flagged assumption in `edap_downloader.fetch_module()`'s docstring -
  now resolved). Module has ~8 broad categories ("Common disclosures", "Financial
  disclosures", ...); Template has one row per specific EBA template code
  ("K_61.00 - EU KM1 - Key metrics template", "K_02.00 - EU CCR1 - ...", ...). Power BI
  cross-filters them: picking a Template narrows Module's own option list (confirmed -
  picking the EU KM1 template narrowed Module down to just "Common disclosures").
- **The popup's option list is virtualized and does not show the full set until you type
  in its own search box** - and the search box must receive real keystrokes
  (`locator.type(..., delay=...)`), not a single `.fill()` call; `.fill()` sets the value
  but the popup's own filtered list never re-renders from it (confirmed - identical,
  unfiltered option list came back after `.fill()`, a correctly filtered list came back
  after `.type()`).
- **Escape does not close a slicer's popup** (confirmed - a popup's options stayed in the
  DOM and polluted the next field's option count after pressing Escape). Re-clicking the
  same trigger toggles it closed instead (confirmed via `aria-expanded` flipping to
  `"false"`).
- **Module doesn't need to be set at all** - Power BI cross-filters it from Template (see
  above), and a live export with only Entity + Template + Reference Date set produced the
  same data as one with Module also explicitly set (confirmed - same row count, same
  byte size to within export-timestamp noise). `DataPointQuery` therefore has no `module`
  field; `_select_slicer` still supports a `"module"` field key internally if a future
  caller ever needs to disambiguate a Template name that collides across two Modules, but
  nothing calls it today.
- **P3DH's own available Reference Dates, as of 2026-10-06, are 30/06/2025, 30/09/2025,
  31/10/2025, 31/12/2025, 31/03/2026, 30/06/2026 - nothing earlier.** This means P3DH
  cannot reproduce or extend the spike's Erste FY2024 (31/12/2024) comparison - that
  period predates P3DH's own data entirely. Once wired in, P3DH is a *third, later-period*
  source, not a drop-in replacement or cross-check for the FY2024 figures already
  reconciled in `spike/comparison.md`.
- **The export control is NOT `#exportFileButton`/`#exportFileButtonContainer`** - those
  exist in the page's same-origin chrome (confirmed present, count 2) but stay invisible
  on the Data Points Report specifically. The real control is the table VISUAL's own
  "more options" menu (`.vcMenuBtn`, inside the Power BI iframe) -> "Export data" menu
  item -> a standard Power BI "Which data do you want to export?" dialog -> its "Export"
  button, which is what actually triggers the browser download.

**Verified end to end on 2026-10-06**: entity="Erste Group Bank AG",
reference_date="31/12/2025", template="K_61.00 - EU KM1 - Key metrics
template" -> a real, structured 198-row .xlsx (columns: Entity Code, Entity Name, Country,
Module Name, ModuleCode, Cell, Template, Row, Row Name, Column, Column Name, Sheet,
FactValue - one row per reported data point, long format, similar shape to the stress
test's own TRA_OTH.csv). This closes out task 1.1's core open questions; what's left is
wiring this into `edap_downloader.fetch_module()` (still a stub) and `run_update.py`.
"""

from __future__ import annotations

import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PWTimeoutError, sync_playwright

DATA_POINTS_REPORT_URL = "https://edap-public.eba.europa.eu/Report/index/MTE2"
POWERBI_IFRAME_SELECTOR = 'iframe[src*="powerbi.com"]'

# Real internal field names (slicer aria-labels), confirmed 2026-10-06 - see module
# docstring. Keys are the public, readable names this module's own API uses.
FIELD_ARIA_LABELS = {
    "reference_date": "ReferenceDate",
    "entity": "ENT_NAM",
    "module": "ModuleName",
    "template": "Template",
}

TRIGGER_SELECTOR = 'div.slicer-dropdown-menu[aria-label="{field}"]'
SEARCH_SELECTOR = "input.searchInput, input[type='text']"  # scoped to one popup
OPTION_SELECTOR = '[role="option"]'  # scoped to one popup

PAGE_NAVIGATION_SELECTOR = '[aria-label*="Page navigation"]'  # the "Go to report" control
# The real export path (confirmed 2026-10-06, replacing an earlier wrong guess -
# #exportFileButton/#exportFileButtonContainer exist on the page but stay invisible on
# this report; the actual control is the TABLE VISUAL's own "more options" context menu):
VISUAL_MENU_BUTTON_SELECTOR = ".vcMenuBtn"
EXPORT_DATA_MENU_ITEM = "Export data"  # role="menuitem" text, inside the visual's menu
EXPORT_DIALOG_CONFIRM_BUTTON = "Export"  # role="button" text, inside the "Which data..." dialog


@dataclass(frozen=True)
class DataPointQuery:
    entity: str  # P3DH's own display/legal name, e.g. "Erste Group Bank AG" - NOT an LEI
    reference_date: str  # e.g. "31/12/2025" - must be one P3DH actually has, see docstring
    template: str  # e.g. "K_61.00 - EU KM1 - Key metrics template" - exact option text
    # No `module` field: Power BI cross-filters Module from Template, and a live export
    # confirmed Module doesn't need to be explicitly set (see module docstring).


def _normalize(text: str) -> str:
    """Lowercase, strip accents, drop everything but letters/digits - so "Banco
    Santander, S.A." and "BANCO SANTANDER S.A." compare equal despite the comma, and a
    name with/without a diacritic (e.g. "Cooperatieve"/"Coöperatieve") compares equal too.
    Needed because GLEIF's resolved legal name (entities.csv's `name` column) frequently
    differs from P3DH's own displayed text in exactly these ways - a literal match
    previously, falsely, reported dozens of real pilot banks as absent from P3DH
    (confirmed 2026-10-06, see module docstring)."""
    nfkd = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return "".join(c for c in stripped.lower() if c.isalnum())


#  Legal-form words common across many unrelated entities - too generic to use as a sole
#  search term (e.g. "BANCO" alone returns every Spanish/Portuguese/Italian bank, burying
#  the one we want outside Power BI's own rendered result window).
_GENERIC_NAME_WORDS = {
    "bank", "banco", "banca", "bankas", "banque", "bankinter", "group", "groep", "gruppe",
    "groupe", "gruppen", "csoport", "holding", "holdings", "societe", "sociedad", "anonyme",
    "anonima", "societa", "per", "sa", "spa", "srl", "nv", "ab", "asa", "oyj", "oy", "publ",
    "plc", "ltd", "nyrt", "the", "and", "of", "azioni", "aktien", "aktiengesellschaft",
    "gesellschaft", "public", "limited", "company",
}
#  Normalized once (accents/punctuation/case stripped), so a raw token like "S.A." (which
#  never literally equals "sa") is still recognized as the same generic word - this was a
#  real bug: "S.A." vs "Sociedad Anonima" both being ignored inconsistently broke the
#  subset check below for BBVA specifically (confirmed 2026-10-06).
_GENERIC_NAME_WORDS_NORM = {_normalize(w) for w in _GENERIC_NAME_WORDS}


def _distinctive_words(text: str) -> set[str]:
    """Normalized words from `text` that aren't generic legal-form boilerplate - the
    proper-noun-like core of a name. Used to tell a genuine legal-name variant (same
    distinctive words, different legal-form suffix, e.g. "AIB Group plc" for "AIB GROUP
    PUBLIC LIMITED COMPANY") apart from a DIFFERENT, more specific entity that merely
    shares a word (e.g. "Societe Generale Bank - Cyprus Ltd" for "SOCIETE GENERALE" -
    "cyprus" is a real, distinguishing extra word, not a legal-form synonym)."""
    return {
        _normalize(w) for w in text.replace("-", " ").split()
        if _normalize(w) and _normalize(w) not in _GENERIC_NAME_WORDS_NORM
    }


def _search_candidates(value: str) -> list[str]:
    """Search terms to try in turn for the `entity` field, most-specific first: the full
    value, then its individual words longest-to-shortest (skipping generic legal-form
    words per `_GENERIC_NAME_WORDS`), then its first word as a last resort. A single
    generic or mismatched term can return far more results than Power BI's popup renders
    at once, hiding the real option even though it exists - trying several is cheap (one
    extra `.type()` + wait each) and far more reliable than guessing one in advance."""
    words = [w.strip(".,") for w in value.split()]
    distinctive = sorted(
        {w for w in words if len(w) > 2 and w.lower() not in _GENERIC_NAME_WORDS},
        key=len, reverse=True,
    )
    candidates = [value, *distinctive, *(words[:1])]
    seen: set[str] = set()
    out = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _select_slicer(page: Page, field_key: str, value: str, timeout_ms: int = 15000) -> None:
    """Open the named slicer, search for an option matching `value` (normalized, see
    `_normalize` - not a literal string match), click it, then close the slicer by
    re-clicking its trigger (toggle - Escape does not close it, confirmed 2026-10-06).

    For `entity` specifically, tries several search terms in turn (`_search_candidates`)
    rather than one guess, since GLEIF's resolved name often doesn't surface the right
    option on the first attempt (see that function's docstring)."""
    aria_label = FIELD_ARIA_LABELS[field_key]
    frame = page.frame_locator(POWERBI_IFRAME_SELECTOR)
    trigger = frame.locator(TRIGGER_SELECTOR.format(field=aria_label))
    trigger.first.click(timeout=timeout_ms)
    time.sleep(1.5)  # popup open animation/mount - without this, is_visible() below reads stale (observed flaky)

    popup_id = trigger.first.get_attribute("aria-controls")
    if not popup_id:
        raise PWTimeoutError(f"slicer '{aria_label}' has no aria-controls popup id")
    popup = frame.locator(f"#{popup_id}")
    options = popup.locator(OPTION_SELECTOR)
    value_norm = _normalize(value)
    value_distinctive = _distinctive_words(value) if field_key == "entity" else set()

    def _try_click_match(term_norm: str) -> bool:
        n = options.count()
        exact_i = None
        word_hits: list[int] = []
        for i in range(n):
            text = options.nth(i).inner_text(timeout=2000)
            text_norm = _normalize(text)
            if text_norm == value_norm:
                exact_i = i
                break  # exact full-value match always wins outright
            # Fallback: the SEARCH TERM (not the full value) as one whole normalized word
            # in the option - handles genuine legal-name variants GLEIF's resolved name
            # doesn't share with P3DH's own text (e.g. "BELFIUS BANQUE" vs P3DH's "Belfius
            # Bank", "AIB GROUP PUBLIC LIMITED COMPANY" vs "AIB Group plc"). Guarded two
            # ways, both confirmed necessary 2026-10-06: it must uniquely identify one
            # option (else a shared common word like "aib" inside an unrelated
            # "...Aibling" name could false-match), AND that option's own distinctive
            # words must be a SUBSET of the value's - without this, "SOCIETE GENERALE"
            # wrongly matched "Societe Generale Bank - Cyprus Ltd" (a real but different,
            # more specific subsidiary: "cyprus" is a genuine extra distinguishing word,
            # not a legal-form synonym the first guard alone can tell apart).
            words = {_normalize(w) for w in text.replace("-", " ").split()}
            if term_norm in words and _distinctive_words(text) <= value_distinctive:
                word_hits.append(i)
        target = exact_i if exact_i is not None else (word_hits[0] if len(word_hits) == 1 else None)
        if target is None:
            return False
        options.nth(target).click(timeout=timeout_ms)
        return True

    # Power BI hides the search box when cross-filtering has already narrowed this
    # slicer's own option list down small (observed on `reference_date` once entity +
    # template were already set) - only search when there's actually a box to use.
    search = popup.locator(SEARCH_SELECTOR)
    search_visible = search.count() > 0 and search.first.is_visible()
    candidates = _search_candidates(value) if field_key == "entity" else [value]

    matched = False
    tried: list[str] = []
    for term in candidates:
        if search_visible:
            search.first.click(timeout=timeout_ms)
            search.first.fill("")  # clear the previous candidate before typing the next
            search.first.type(term, delay=80)  # NOT .fill() for the query itself - the popup's list only re-renders from real keystrokes
            time.sleep(2.5)  # debounce - Power BI's own filtering is not instant, and is itself not fixed-latency (observed flaky at 1.5s)
        tried.append(term)
        if _try_click_match(_normalize(term)):
            matched = True
            break
        if not search_visible:
            break  # no search box to refine with - one attempt is all there is

    if not matched:
        trigger.first.click(timeout=timeout_ms)  # best-effort close before raising
        raise PWTimeoutError(
            f"slicer '{aria_label}': no option matching {value!r} after trying search "
            f"term(s) {tried} - check against the field's real option text (see this "
            f"module's docstring for how the search box works)."
        )

    time.sleep(0.5)
    trigger.first.click(timeout=timeout_ms)  # close (toggle, not Escape)
    time.sleep(0.5)


def export_data_points(query: DataPointQuery, out_dir: Path, headless: bool = True) -> Path:
    """Set the four filters, navigate to the report, and trigger the table visual's own
    "Export data" (via its `.vcMenuBtn` context menu, not the page-level
    `#exportFileButton`, which exists in the DOM but stays invisible on this report),
    confirm the export dialog, and save the downloaded file under out_dir.

    Verified end to end against the live page on 2026-10-06 (Erste Group Bank AG / EU KM1
    / 31/12/2025 -> a real 198-row structured .xlsx). See module docstring for the full
    investigation trail and DATA_SOURCES_NOTES.md's matching dated entry.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(accept_downloads=True)
        page.goto(DATA_POINTS_REPORT_URL, wait_until="load")
        page.wait_for_selector(POWERBI_IFRAME_SELECTOR, timeout=30000)
        time.sleep(5)  # Power BI's own internal render, not just the iframe's load event

        for field_key, value in [
            ("entity", query.entity),
            ("template", query.template),
            ("reference_date", query.reference_date),
        ]:
            try:
                _select_slicer(page, field_key, value)
            except PWTimeoutError as exc:
                browser.close()
                raise PWTimeoutError(
                    f"Could not set slicer '{field_key}' to {value!r}: {exc}"
                ) from exc

        frame = page.frame_locator(POWERBI_IFRAME_SELECTOR)
        frame.locator(PAGE_NAVIGATION_SELECTOR).first.click(timeout=15000)
        time.sleep(6)  # the actual report/table visual renders here, not just the page nav

        frame.locator(VISUAL_MENU_BUTTON_SELECTOR).first.click(timeout=15000)
        time.sleep(1)
        frame.get_by_role("menuitem", name=EXPORT_DATA_MENU_ITEM).click(timeout=15000)
        time.sleep(2)  # the "Which data do you want to export?" dialog renders here

        with page.expect_download(timeout=30000) as download_info:
            frame.get_by_role("button", name=EXPORT_DIALOG_CONFIRM_BUTTON).click(timeout=15000)
        download = download_info.value
        safe_entity = query.entity.replace(" ", "_").replace("/", "-")
        dest = out_dir / f"{safe_entity}_{query.template[:10]}_{query.reference_date.replace('/', '-')}.xlsx"
        download.save_as(dest)
        browser.close()
        return dest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entity", help='P3DH display name, e.g. "Erste Group Bank AG" - not an LEI')
    parser.add_argument("reference_date", help='e.g. "31/12/2025" - must be in P3DH\'s current range')
    parser.add_argument("template", help='exact option text, e.g. "K_61.00 - EU KM1 - Key metrics template"')
    parser.add_argument("--out-dir", default="data/raw/p3dh")
    parser.add_argument("--headed", action="store_true", help="watch it run")
    args = parser.parse_args()

    result = export_data_points(
        DataPointQuery(args.entity, args.reference_date, args.template),
        Path(args.out_dir),
        headless=not args.headed,
    )
    print(f"saved to {result}")
