# Pillar 3 Data Hub — bulk download: findings and plan

Dated 2026-09-17. Written after directly inspecting the live EDAP portal (not just its
published user guides), because the guides stop short of documenting programmatic access.

## What EDAP actually is

`https://edap-public.eba.europa.eu` is **not** a REST API or a file server. Every page under
"Pillar 3 Data HUB" (`Official Data and Templates Visualisation`, `Data Points Report`) is a
Microsoft **Power BI report embedded via `app.powerbi.com/reportEmbed`**, served to an
anonymous `Public Access` role. Confirmed by inspecting the page's own DOM: the report iframe
points at a specific `reportId` + `groupId` (workspace) on Power BI's West-Europe cluster.

Consequences for "bulk download":

- There is **no documented public REST/JSON API** for querying "all data for all LEIs."
  The official user guides (EBA User Guide — Large and Other Institutions; EDAP visualisation
  tools guide) describe downloading "the original files submitted by institutions (PDF and
  XBRL-CSV, packaged per module as .zip)" but never give a URL pattern, auth scheme, or bulk
  endpoint — and neither guide nor the portal's own DOM exposes one.
- The only self-service export mechanism visible in the DOM is Power BI's native
  **"Export data"** button (`#exportFileButton`) on each report/visual. That's a per-visual,
  UI-driven export subject to Power BI's normal row caps (tens of thousands of rows, not a
  full-database dump) — fine for spot checks, not for "all LEIs, all periods, all modules."
- The `Data Points Report` page (report id 116) is a filtered lookup (Entity × Module ×
  Reference Date × Template) — useful for verifying a single figure, not for enumerating the
  full set of reporting entities.
- Cross-origin iframe traffic to `app.powerbi.com` isn't inspectable from the parent page with
  the tools available, so I could not confirm whether a lower-level Power BI query endpoint is
  reachable without a signed embed token. Public/anonymous Power BI embeds generally *don't*
  expose that without an Azure AD-issued token the public portal doesn't hand out — so I'm not
  building on top of that; it would be fragile and likely against the portal's terms of use at
  any real volume.

**Bottom line:** as of today, there's no clean bulk API. This matches the README's own listed
risk ("difficulty obtaining or processing bulk regulatory reporting data") — it's real, not
hypothetical, and worth stating explicitly in the project's risk log.

## Recommended path

1. **Ask EBA directly.** Their own user guide points bulk/API questions to
   `P3DH@eba.europa.eu`. Many EU regulators run a separate bulk/SFTP or API channel for
   researchers that isn't advertised on the public dashboard. This costs one email and might
   remove the whole problem — send it before investing more engineering time.
2. **Don't try to enumerate "all LEIs" from EDAP itself.** Get the entity universe from a
   source built for that: the EBA **Credit Institutions Register** (also on EDAP, same
   Power-BI caveats) or, for enrichment/validation of any LEI you already have, **GLEIF's**
   real, documented, public API/bulk files (`api.gleif.org`, Golden Copy CSV/XML downloads at
   gleif.org — no key required). GLEIF won't tell you *which* banks are in Pillar 3 scope, but
   it will validate/enrich any LEI you already have (legal name, country, status).
3. **Build the pipeline around a state file, not a full re-crawl.** Regardless of how the
   actual download call ends up working (official bulk channel, or scripted per-visual
   export), structure the code so it: (a) knows the *expected* publication calendar, (b) knows
   what it already has, (c) only attempts what's new. That's `waves.py` + `state/` below.
4. **Treat the actual EBA fetch as a swappable adapter.** `edap_downloader.py` is deliberately
   a thin interface with one real implementation path documented and one experimental one
   (Playwright-driven UI export) clearly marked as unverified — swap in the real bulk endpoint
   there once EBA responds, without touching the scheduling/state logic.

## Publication calendar ("waves"), per Article 4 of the EBA's P3DH ITS

- Year-end (December reference date) disclosures: due **T + 6 months** (end-June).
- Remuneration data: due **T + 8 months** (end-August).
- Quarterly reference dates: due **T + 4 months**.
- Semi-annual reference dates: due **T + 4 months**.

`waves.py` encodes this so the update script can compute "the next wave we should check for"
instead of polling blindly.

## Update 2026-09-17: two more sources, both confirmed real and bulk-downloadable

Per the project's current direction ("as complete as possible compilation of publicly
available data" - final inclusion decisions deferred), added two more EBA programmes.
Unlike P3DH, both were verified by directly fetching their landing pages and following the
actual links - not by guessing a pattern - and both hand back genuinely large files (>30MB),
confirming they're real bulk datasets, not just a summary table.

**EU-wide Transparency Exercise** (`data_acquisition/eba_exercises.py`, `exercise="transparency"`).
Bank-by-bank, LEI-tagged CSVs (credit risk, market risk, sovereign exposures, other templates)
plus a data dictionary, for every edition from 2013 through 2025. **Discontinued from June
2025** - EBA points users to P3DH going forward - so this is a closed, static archive. That
makes it ideal for the reproducible test fixtures the README asks for, not for live updates.

**EU-wide Stress Test** (same module, `exercise="stress_test"`). Same structure (bank-level
CSVs + per-bank PDFs), still active, but biennial - editions in 2023 and 2025, next expected
~2027 - and NOT a plain reported actual: figures are scenario-projected (baseline/adverse
capital, P&L, RWA paths), so they are a different *kind* of figure than Pillar 3/ESEF
actuals. Treat as non-comparable by default in the reconciliation logic; this is a live
instance of the exact "similar-looking variables, different economic meaning" risk the
README's section 5 already names.

**A genuinely useful side effect:** each participating bank's individual result is a PDF
whose *filename* encodes country + LEI (e.g. `DE_7LTWFZYICNSX8D621K86_TR_2025.pdf`,
`EBA_ST_DE_7LTWFZYICNSX8D621K86.pdf` for Deutsche Bank AG). That means the landing page
itself is a real, EBA-sourced entity list for whichever population of banks was in scope
that year - `eba_exercises.build_entities_csv()` scrapes it to populate `data/entities.csv`
automatically, which is more authoritative than guessing bank names against GLEIF (though
GLEIF is still useful to fill in the legal name once you have the LEI).

Verified working URLs as of today (2025 editions):
- Transparency 2025 full database: `eba.europa.eu/assets/TE2025/Full_database/883401/{tr_cre,tr_mrk,tr_sov,tr_oth}.csv`
- Stress Test 2025 full database: `eba.europa.eu/assets/st25/full_database/763451/{TRA_CRE_IRB,TRA_CRE_STA,TRA_OTH}.csv`

Landing-page URLs are NOT a guessable pattern year to year (naming is inconsistent - compare
`.../2020-eu-wide-transparency` vs `.../2018-eu-wide-transparency-exercise`), so
`eba_exercises.EXERCISES` is a maintained registry, not a formula. It currently covers every
year back to 2010/2013; add a line when EBA publishes a new one.

## Update 2026-09-19: no reply from EBA yet - starting the P3DH scraper

No response from P3DH@eba.europa.eu as of today, so `edap_downloader.fetch_module()` now
calls a real (but unverified end-to-end) Playwright scraper, `data_acquisition/edap_scraper.py`,
instead of raising. Two things worth recording about *why* this had to be Playwright
specifically, since they shape what to expect from it:

1. I tried to drive the "Data Points Report" page live with this session's own browser
   tooling first. It confirmed something important: the four filter dropdowns (Entity,
   Entity Module, Reference Date, Template) live *inside* the cross-origin
   `app.powerbi.com/reportEmbed` iframe, and this session's DOM/accessibility tools
   (`read_page`, `find`) come back completely empty against it - not just unstyled, actually
   empty. Coordinate-based clicking on screenshots didn't reliably land on the right control
   either. That rules out any simple "inspect the page and script it" approach.
2. Playwright doesn't have that limitation - it drives Chrome over the DevTools Protocol, so
   `page.frame_locator(...)` can reach into a cross-origin iframe's real DOM regardless. That
   is the whole reason the scraper has to be a standalone local script rather than something
   built and verified from inside this session: it needs a browser Playwright can attach to
   *and* real network access to eba.europa.eu / powerbi.com, and this sandboxed session's own
   network egress is blocked from reaching either (confirmed - a direct `requests.get` and a
   local headless Playwright launch both hit `ERR_TUNNEL_CONNECTION_FAILED` against
   edap-public.eba.europa.eu when tested here).

Net effect: `edap_scraper.py` is a real, runnable Playwright script encoding the *standard*
Power BI dropdown-slicer automation pattern (a `role="listbox"` trigger opening a
`role="option"` popup), but I could not verify that pattern against this specific report's
actual internal markup - not from this session (network-blocked) and not from the in-chat
browser (DOM-blind on that iframe). One thing I *did* confirm directly: the "Export data"
trigger (`#exportFileButton`) is part of EDAP's own same-origin page chrome, shared across
every `/Report/index/*` page via its `reportTemplate.js` - so that part of the script should
be solid; the four slicer selectors are the part most likely to need a fix.

**Before trusting this in `run_update.py`'s loop:** run it once by hand with `--headed` -

    python -m data_acquisition.edap_scraper "<some LEI>" "<module>" "<ref date>" "<template>" --headed

- watch what actually happens, and if a slicer selector doesn't match (it'll raise a
  `TimeoutError` naming exactly which field failed), run
  `playwright codegen https://edap-public.eba.europa.eu/Report/index/MTE2` locally, redo the
  same four selections while it records, and copy the selectors it captures into
  `SLICER_SELECTORS` in `edap_scraper.py`. Also still unconfirmed: whether the "Entity"
  slicer expects an LEI or a display name, and whether "Module" and "Template" are actually
  the same list or two different ones (`fetch_module()` currently assumes they're the same,
  flagged with a comment) - the first `--headed` run will answer both.

## Update 2026-09-22: EBA P3DH team replied directly - three questions answered

Emailed P3DH@eba.europa.eu on 2026-09-19 asking three direct questions (bulk/API access,
a complete institution list, and whether the ITS T+4/6/8 calendar is reliable). Got a real
reply from the "EBA P3DH Team" on 2026-09-22. Recording the substance here since it changes
how much weight to put on assumptions already baked into this project:

1. **Bulk download / API access.** "Discussions regarding the possible implementation of a
   bulk download solution and/or API access are currently ongoing. However, at this stage,
   we cannot commit to the introduction of such functionality or provide any timeline for
   its availability." For now: "accessing and downloading the data through the available
   EDAP/P3DH functionalities" (i.e. the dashboard) is the only sanctioned path. This upgrades
   `edap_scraper.py` from "fallback until the real API ships" to "the access method,
   indefinitely" - there's an open internal discussion, not a committed near-term
   alternative. Worth re-emailing again in a few months to check status, but not worth
   designing around an assumption it'll land soon.

2. **Complete list of in-scope institutions.** "At present, the institutions visible in the
   Data Hub are those that have already published Pillar 3 disclosures through the
   platform. We are not in a position to provide a separate or complete list of institutions
   beyond what is publicly available in the Data Hub." So there is no better entity-discovery
   source than the Hub itself - confirms the EBA Transparency Exercise participant list
   (`eba_exercises.build_entities_csv()`) remains the best available seed, but it's a proxy,
   not the ground truth: P3DH onboarding is still rolling out (e.g. SNCI onboarding hasn't
   even piloted yet as of this writing), so "in the 2025 Transparency Exercise" and "live on
   P3DH now" are not guaranteed to be the same set in either direction. Once
   `edap_scraper.py` is verified (task 1.1), its own Entity slicer is the actual ground
   truth for "who's live on P3DH" and `entities.csv` should be cross-checked against it,
   not assumed correct because it came from an EBA source.

3. **Is the ITS T+4/6/8 calendar reliable?** "The timelines set out in the ITS... should be
   understood as an EBA expectation rather than a strict legal publication requirement." In
   other words, `waves.py`'s calendar is a scheduling heuristic ("don't bother checking
   before this date"), not a guarantee data will actually appear by then. Checked
   `run_update.py` directly: right now a wave that hasn't published yet falls into the same
   generic `except Exception` branch as a genuine scraper break, and both get recorded as
   `status: "failed"` in `download_log.json` with no way to tell them apart. Given EBA just
   confirmed late waves will be routine rather than exceptional, that conflation needs
   fixing - a late-but-expected wave and an actually-broken scraper are different problems
   requiring different responses, and burying the second inside a pile of the first is a
   real risk to notice a real break.

   EBA pointed to FAQ B1 on the P3DH page for more detail on timing. An automated fetch of
   that page produced numbers that didn't fully match this project's own records, and was
   flagged here as unverified (2026-09-22, earlier same day) - correctly, as it turned out:
   the user read the FAQ by hand and supplied the real text below, published 2026-05-22.

   **FAQ B1** (transitional-period submissions): "Once the onboarding process is completed
   and the institution is under conditions to submit the information to the EBA, the reports
   for the past reference dates covered by the transitional arrangements shall be submitted
   to the EBA for publication in the data hub. While no limit date is set for this
   submission, reports already made public by the institution are expected to be submitted
   without undue delay and reports not yet published should follow the timeline envisaged
   for the steady state."

   **FAQ B2** (steady-state submissions): required information is due "on the same day on
   which institutions publish their financial statements... or as soon as possible
   thereafter"; Article 450 (remuneration) information is due "no later than two months
   after" the institution's own financial-statement publication date. "While no mandatory or
   indicative limit dates for submission are put in place," the ITS final report's
   expectations are:
   - Year-end reports (December reference date): end-June; remuneration info: end-August.
   - Year-end reports (reference date **other than** December): reference date + 6 months;
     remuneration info: reference date + 8 months.
   - Quarterly reports: reference date + 4 months.
   - Semi-annual reports: reference date + 4 months.

   This confirms `waves.py`'s existing `_DEADLINE_MONTHS` table (quarterly=4,
   semi_annual=4, year_end=6, year_end_remuneration=8) is correct for December-referenced
   waves. It also surfaces a gap: `waves.py`'s `_reference_dates_since()` only tags `month
   == 12` dates as `YEAR_END`/`YEAR_END_REMUNERATION` - it has no path for a bank whose
   fiscal year-end reference date isn't December, even though FAQ B2 explicitly covers that
   case ("reference date + 6/8 months" instead of the fixed end-June/end-August shortcut).
   Likely a non-issue for v1's pilot banks (EU banks overwhelmingly report on a calendar
   fiscal year), but worth confirming rather than assuming - see the new task in
   `add-mvp-v1`'s tasks.md.

## Sources checked

- https://www.eba.europa.eu/publications-and-media/press-releases/eba-pillar-3-data-hub-goes-live
- https://www.eba.europa.eu/risk-and-data-analysis/pillar-3-data-hub
- EBA User Guide (Large and Other Institutions), Jan 2026
- EBA User Guide — EDAP visualisation tools for Pillar 3 reports, Jan 2026
- Live inspection of https://edap-public.eba.europa.eu (Report/index/MTE1, Report/index/MTE2)
- https://www.gleif.org/en/lei-data/gleif-api and https://www.gleif.org/en/lei-data/gleif-golden-copy
- https://www.eba.europa.eu/eu-wide-transparency-exercise-0 (full link listing fetched directly)
- https://www.eba.europa.eu/eu-wide-stress-test-2025 (full link listing fetched directly)
- ECB Supervisory Banking Statistics (SUP dataset): https://data.ecb.europa.eu/data/datasets/SUP/data-information - checked and excluded, aggregated across all significant institutions only, no per-bank figures (confidentiality)
- Direct email reply from P3DH@eba.europa.eu ("EBA P3DH Team"), received 2026-09-22, in
  response to a question sent 2026-09-19
- https://www.eba.europa.eu/risk-and-data-analysis/pillar-3-data-hub, FAQ B1 and B2
  (published 2026-05-22) - read directly by the user, see 2026-09-22 entry above

## Update 2026-10-06: pilot sample trimmed via S&P's top-50 European banks list

Moving from the spike back to the main MVP work (task 1.2's "trim to pilot banks" step,
AGENTS.md "Immediate next steps" #2), the user supplied S&P Global Market Intelligence's
"Europe's 50 largest banks by assets" (2026 edition) as the trimming criterion, including
headquarters country and total assets for all 50 - the article itself
(spglobal.com/.../europes-50-largest-banks-by-assets-2026) returns HTTP 403 (paywalled);
secondary sources (consultancy.eu, wall-street.ro, borsaefinanza.it) only reproduce the
top ~10-20 names, not the full table, so the user's pasted table is the only complete,
citable version of this list used here.

**Step 1 - exclude by jurisdiction, not by lookup.** 13 of the 50 are headquartered outside
the EU/EEA: UK (HSBC, Barclays, Lloyds, NatWest, Standard Chartered, Nationwide - 6),
Switzerland (UBS, Raiffeisen Gruppe Switzerland, Zurcher Kantonalbank - 3), Russia (Sberbank,
VTB, Gazprombank - 3), Turkiye (Ziraat Bankasi - 1). None of EBA's programmes (Transparency
Exercise, Stress Test, P3DH) cover non-EU/EEA institutions, so these are excluded by the
scope of EBA's remit, not by any missing-data check - no lookup was needed to rule them out.

**Step 2 - cross-check the remaining 37 against the existing 64-bank Stress Test 2025
sample.** `data/entities.csv` already had 64 real, LEI-tagged banks from the Stress Test
2025 participant list (2026-09-25 entry above), but with a blank `name` column - it was
populated LEI-first and never resolved to legal names. Resolving all 64 via GLEIF
(`lei-records/{lei}`) first, then matching the S&P names against that known-good list by
hand, turned out to be far more reliable than searching GLEIF by the S&P bank names directly:
GLEIF's `filter[entity.legalName]` is near-exact and missed obvious matches (e.g. "BNP
Paribas SA" vs. GLEIF's registered "BNP PARIBAS"), and its `filter[fulltext]` fallback
returned irrelevant top hits (e.g. "BNP Paribas SA" surfaced "PUBLICIS GROUPE SA" as the top
fulltext result for one query) - fuzzy search over ~2.7M global LEI records is not reliable
enough to trust unattended, consistent with `gleif_client.py`'s own docstring warning not to
trust a single top match blindly.

**Result: all 37 EU/EEA banks from S&P's top 50 already resolve to an entity in the existing
64-bank list** - the Stress Test 2025 sample (EBA's "representative" sample, ~75-80% of EU
banking assets by design) turns out to already be a superset of S&P's top-50-by-assets EU/EEA
subset. No new entity discovery was needed; the actual work was annotation, not expansion.

**Found along the way: a real bug in EBA's own published data, not in this project's code.**
Two of the 64 LEIs didn't resolve at GLEIF at all (404) - both French: `FR9695005MSX1OYEMGDF`
(labelled "Groupe BPCE" in the source row) and `FR969500TJ5KRTCJQWXH` (labelled "Groupe Credit
Agricole"). Grepping `data/raw/stress_test/2025/TRA_OTH.csv` directly confirmed these strings
are exactly what EBA's own bulk file contains (not introduced by `eba_exercises.py`'s
parsing) - e.g. `"FR","FR9695005MSX1OYEMGDF","Groupe BPCE","202412","2531004","1","","3606.22..."`.
Both corrupted values are 20 characters, the correct length for an LEI, which is why no
earlier length check caught them. GLEIF fulltext search for "BPCE" and "Credit Agricole"
found the real LEIs - `9695005MSX1OYEMGDF46` (legal name "BPCE") and `969500TJ5KRTCJQWXH05`
(legal name "CREDIT AGRICOLE SA") - and the pattern is now obvious once seen: EBA's stored
value is the 2-letter country code prepended to the first 18 characters of the real LEI, with
the real LEI's last 2 (check-digit) characters silently dropped. Checked the rest of the
64-LEI universe for the same signature (LEI starting with its own row's country code) - no
other instances. Both rows in `entities.csv` were corrected directly to the real LEIs, with
the investigation recorded in each row's own `notes` field rather than filed away separately,
so anyone re-deriving `entities.csv` later (e.g. by re-running `build_entities_csv()`) would
hit the same two 404s and should know to re-apply this fix rather than silently losing two of
the largest banks in the sample. Not reported to EBA; worth doing if this project continues
past the course.

**Schema change:** `data/entities.csv` gained an `sp50_2026_rank` column (blank where a bank
isn't in the S&P list) and `data_acquisition/entities.py`'s `Entity` dataclass gained the
matching field. `name` is now filled in for all 64 rows (GLEIF legal names), where it was
blank before. `python -m data_acquisition.entities` and the full test suite were re-run after
the change (64/64 validate against GLEIF; 8/8 tests pass) - the schema change is additive
(new field has a default), so nothing downstream broke.

Sources checked (this update):
- S&P Global Market Intelligence, "Europe's 50 largest banks by assets" (2026 edition) -
  full ranked table (rank, company, HQ country, accounting principle, total assets $B)
  supplied directly by the user; the source URL itself 403s on direct fetch.
- https://api.gleif.org/api/v1/lei-records (record lookup for all 64 existing entities.csv
  LEIs, plus fulltext/legalName search for the 37 S&P EU/EEA bank names and, separately, for
  "BPCE" and "Credit Agricole" to resolve the two corrupted LEIs)
- `data/raw/stress_test/2025/TRA_OTH.csv` (direct grep, to confirm the two corrupted LEI
  strings originate in EBA's own published file, not in this project's parsing)

## Update 2026-10-06: P3DH scraper verified end to end (task 1.1 closed out)

The 2026-09-19 entry above concluded this session's network egress was blocked to both
`edap-public.eba.europa.eu` and `app.powerbi.com`, so `edap_scraper.py` was written as an
unverified skeleton. Re-checked today before starting this work: both hosts now return
HTTP 200 from this session (`requests.get` succeeded directly). Whatever blocked it in
September is no longer in effect - installed Playwright + Chromium
(`pip install playwright && python -m playwright install chromium`) and drove the real
page headlessly.

**Phase 1 - page structure.** `https://edap-public.eba.europa.eu/Report/index/MTE2` has
exactly 2 frames: the EDAP page itself and one `app.powerbi.com/reportEmbed` iframe
(~950KB of rendered markup). A screenshot showed 4 visible filter dropdowns ("Ref Date",
"Entity Name", "Module Name", "Template") plus a "Go to report" action - a materially
different flow than the original skeleton assumed (which expected the filters and an
export button on the same view).

**Phase 2 - real selectors.** Each filter is a Power BI slicer,
`div.slicer-dropdown-menu[role="combobox"]`. Their `aria-label`s (confirmed by reading the
rendered DOM directly) are the INTERNAL field names, not the visible header text:
`ReferenceDate` ("Ref Date"), `ENT_NAM` ("Entity Name"), `ModuleName` ("Module Name"),
`Template` ("Template") - the original skeleton's guessed field names ("Entity", "Entity
Module", "Reference Date") were wrong for 3 of 4. Clicking a trigger opens a popup
(`id` from the trigger's own `aria-controls`) containing a scoped search input and
`[role="option"]` items - but the option list is virtualized, showing only ~8 items until
you type in the popup's own search box. Pressing Escape does NOT close the popup (a stale
popup's options polluted the next field's option count when tested) - re-clicking the same
trigger toggles it closed instead (confirmed via `aria-expanded` flipping to `"false"`).

**Phase 3 - search behavior, and the two open design.md questions answered.**
`.fill()` on the search input does not trigger Power BI's own filtering (identical,
unfiltered list came back regardless of the query); `.type(value, delay=...)` (real
per-character keystrokes) does. With that fixed: searching Entity for "Erste" returned 5
real matches ("Erste Group Bank AG" among them); searching Entity for Erste's actual LEI
(`PQOH26KWDF7CG10L6792`) returned zero - **Entity is selected by display/legal name, not
LEI**, settling design.md's first open question. Searching Template for "KM1" returned
exactly one match, "K_61.00 - EU KM1 - Key metrics template" - confirming the naming
convention and that this exact template (used in the spike's Cause 2 section) is
selectable on P3DH. Separately, Module (~8 broad categories: "Common disclosures",
"Financial disclosures", etc.) and Template (one row per specific EBA code) are
confirmed-different lists, and Power BI cross-filters them - selecting the EU KM1 template
narrowed Module's own option list down to just "Common disclosures" - settling design.md's
second open question.

**Phase 4 - a genuine data gap, not a code bug.** P3DH's own available Reference Dates,
queried directly from the slicer's option list, are 30/06/2025, 30/09/2025, 31/10/2025,
31/12/2025, 31/03/2026, 30/06/2026 - nothing earlier. P3DH launched January 2026 and
apparently did not backfill historical periods. This means P3DH **cannot** reproduce or
extend the spike's Erste FY2024 (31/12/2024) comparison in `spike/comparison.md` - that
period predates P3DH's own data entirely. Once wired into `reconcile.py`, P3DH is a third,
*later-period* source, not a cross-check for figures already reconciled there.

**Phase 5 - full end-to-end export, the actual control found by trial.** The skeleton's
assumed export control (`#exportFileButton`/`#exportFileButtonContainer`, same-origin page
chrome) does exist in the DOM (confirmed present, count 2) but stays invisible on this
specific report. After setting all filters and clicking the "Page navigation" / "Go to
report" control (`[aria-label*="Page navigation"]`), the actual report page renders a real
data table - the correct control is the table VISUAL's own "more options" menu
(`.vcMenuBtn`, found by testing selector candidates against the live DOM), which opens a
`role="menuitem"` list including "Export data". Clicking it opens Power BI's standard
"Which data do you want to export?" dialog (radio choices: current layout / summarized /
underlying - underlying disabled, "The report author turned this option off"); clicking its
"Export" button triggers a real browser download.

**Verified twice, independently, via the actual shipped `edap_scraper.py` CLI** (not just
ad-hoc inline scripts): `python -m data_acquisition.edap_scraper "Erste Group Bank AG"
"31/12/2025" "K_61.00 - EU KM1 - Key metrics template"` -> a real 198-row, 14-column .xlsx
(`Entity Code, Entity Name, Country, Module Name, ModuleCode, Cell, Template, Row, Row
Name, Column, Column Name, Sheet, FactValue` - one row per data point, long format, similar
shape to the stress test's own `TRA_OTH.csv`). Sanity-checked the actual figures: CET1
capital (row "1. Common Equity Tier 1 (CET1) capital", column "a. T" = current period) =
EUR 28,523,937,380.03 for 31/12/2025, up from the spike's Dec-2024 actual of EUR 23,995.67m
- a plausible ~19% year-on-year increase, not a red flag.

**A real simplification found along the way:** a live export with only Entity + Template +
Reference Date set (Module left completely unfiltered) produced the same data as one with
Module also explicitly set (same row count, same byte size to within export-timestamp
noise) - confirming Module doesn't need to be tracked as an independent input at all.
`edap_scraper.DataPointQuery` has no `module` field as a result; `edap_downloader.py`'s
`fetch_module()` keeps that parameter name only for compatibility with `run_update.py`'s
existing per-(entity, wave, module) loop shape, but treats its value as the exact P3DH
Template text, not a short code - `data/modules.txt`'s own format changed to match (one
exact Template option string per line, not "CODIS"/"FINDIS"-style codes). Renaming the
parameter and the file throughout the codebase was deliberately deferred rather than done
in the same pass as the scraper verification - noted as follow-up, not done silently.

**What's still open after this**: `data/modules.txt` has one verified entry (EU KM1) for
one bank; task 1.3 needs the rest of the pilot banks' actual submitted templates. The
not-yet-published-vs-failed distinction (task 1.4) and non-December fiscal year-ends (task
1.5) are unaffected by any of this and remain open. `run_update.py` itself has not been run
for a full real pass yet (only `edap_scraper`/`edap_downloader` were exercised directly).

Sources checked (this update):
- Live inspection of `https://edap-public.eba.europa.eu/Report/index/MTE2` and its embedded
  `app.powerbi.com/reportEmbed` iframe, via a real local headless Chromium (Playwright
  1.63.0 + Chrome Headless Shell), including full-page screenshots and raw frame HTML dumps
  saved for inspection during the investigation.
- The actual downloaded export file (`data.xlsx` / similarly named), opened and inspected
  with pandas to confirm it's genuine structured data, not an error page or empty template.

## Update 2026-10-06 (later same day): ESEF populated for 28 more pilot banks

`esef_client.py` had only ever been exercised for one bank (Erste). Checked
`filings.xbrl.org` directly for all 37 S&P-ranked pilot banks (one HTTP call per LEI to
`/api/entities/{lei}/filings`, not an assumption) before fetching anything, to avoid
wasting bandwidth guessing at a period that might not exist for a given bank.

**Result: 29 of 37 have a FY2024 (2024-12-31) filing indexed; 8 don't, in two different
ways worth distinguishing:**

- **6 have NO filing indexed at all, for any year**: Deutsche Bank AG and Commerzbank AG
  (0 filings each), and Confederation Nationale Credit Mutuel, DZ BANK AG, Landesbank
  Baden-Wurttemberg, and Bayerische Landesbank (404 on the filings-list endpoint itself -
  the LEI isn't a known filer at all on this index). **5 of these 6 are German** - this is
  the first *direct, empirical* confirmation of the Germany gap AGENTS.md has flagged since
  the project's original research phase as an unconfirmed guess from documentation. It's
  now a confirmed, 100%-of-sample finding for this project's specific German pilot banks,
  not a guess. The 6th (Credit Mutuel) is a cooperative confederation, structurally similar
  to BPCE and Credit Agricole (see the earlier 2026-10-06 LEI-bug entry) - plausibly its
  consolidated IFRS statements are filed under a different legal entity's LEI than the
  confederation's own, the same way BPCE/Credit Agricole's *stress-test* LEIs turned out to
  need correction. Not pursued further here - flagged as a candidate for the same kind of
  investigation if ESEF coverage for Credit Mutuel becomes a priority.
- **2 have filings indexed, but not for 2024-12-31 specifically**: Societe Generale (has
  2021/2022/2023/2025 - 2024 itself is absent, an odd single-year gap, not a general
  non-coverage) and Intesa Sanpaolo (only has 2021/2022 - nothing since). Both are
  `missing_from_source` for the ESEF side at period 202412 under the current single-period
  design, which is the correct, honest outcome - not a bug in this project's code.

**Fetched and cached the other 28** (Erste already was) via `esef_client.fetch_facts()` -
706MB total under `data/raw/esef/`, average ~1.9s and ~25MB per filing. All 28 succeeded on
the first attempt - no retries, no `EsefDataError`s.

**Concept coverage per bank is uneven, and checked rather than assumed to be complete**:
of the 4 ESEF-side concepts (`Assets`, `Equity`, `InterestRevenueExpense`, `ProfitLoss`),
18 of the 28 report all 4 as undimensioned totals; `Assets` and `ProfitLoss` are universal
(28/28 each); `Equity` and `InterestRevenueExpense` are not:

- **7 banks (BNP Paribas, Credit Agricole, BPCE, La Banque Postale, Danske Bank, Nykredit,
  Belfius) have no undimensioned `ifrs-full:InterestRevenueExpense` fact.** Checked BNP
  Paribas's actual tagged concepts directly (not inferred): it reports
  `ifrs-full:RevenueFromInterest` and `ifrs-full:InterestExpense` as two SEPARATE gross
  figures, never netted into one tagged fact. This is a genuine presentation choice (gross
  interest disclosure), not a missing tag to work around - computing "net interest income"
  as revenue-minus-expense here would be exactly the kind of cross-source/cross-concept
  combination README.md section 3 rules out as a non-goal, so `CONCEPT_MAP` was
  deliberately NOT extended to derive it. `missing_from_source` is the correct, honest
  status for these banks' `net_interest_income` row from `esef`, not a gap to patch.
- **4 banks (UniCredit, Banca Monte dei Paschi, Banco BPM, BPER - all four of this
  project's Italian pilot banks) have no undimensioned `ifrs-full:Equity` fact, and also
  none of `ifrs-full:EquityAttributableToOwnersOfParent`.** Checked UniCredit's full
  concept namespace directly: only `ifrs-full:` and a generic `ext:` (entity extension)
  prefix are used, and no equity-like concept exists under either by substring search. Most
  likely total equity is only ever tagged as a presentation-level roll-up of its components
  (share capital, reserves, NCI, etc.) rather than as its own single fact - a common XBRL
  pattern - but this wasn't confirmed further; logged as a genuine, checked
  `missing_from_source` rather than a bug.

**Confirmed end to end, not just "fetched"**: ran
`reconcile.get_financial_data(lei, SUPPORTED_CONCEPTS, period="202412")` for 3 of the newly
cached banks (BNP Paribas, UniCredit, Santander). All return real rows with the correct
`status` per concept (including the gaps just described, correctly tagged
`missing_from_source`, never fabricated) - **no code changes to `reconcile.py` or
`CONCEPT_MAP` were needed**, since the concept-mapping table was already bank-agnostic
(keyed on source + item code, not on which bank). The same cross-source pattern from the
spike repeats here too: Santander's net interest income is EUR 46,789.74m (stress test)
vs. EUR 46,668.0m (ESEF), a 0.26% gap - small, real, and in the same direction/magnitude
family as Erste's, not something to read into further without the same kind of checking
the spike's Cause 1 correction required.

Sources checked (this update):
- `https://filings.xbrl.org/api/entities/{lei}/filings` for all 37 S&P-ranked LEIs in
  `entities.csv` (one call per bank, to discover actual available periods before fetching)
- `https://filings.xbrl.org` xBRL-JSON filings for the 28 banks fetched (full facts, not
  samples) - cached under `data/raw/esef/<lei>/2024-12-31/facts.json`
- Direct inspection of BNP Paribas's and UniCredit's actual tagged concept namespaces (not
  assumed) to confirm the InterestRevenueExpense/Equity gaps are genuine reporting-format
  differences, not retrieval bugs

## Update 2026-10-06 (third entry, same day): first real run_update.py pass

With `edap_scraper.py`/`edap_downloader.py` verified in isolation, ran `run_update.py`
itself for the first time - the actual scheduled pipeline (state tracking, idempotency),
not just a direct call into the scraper. Found and fixed two real things before trusting
it at scale, plus two genuine new source-coverage findings.

**Bug found by running it for real: `waves.py` generated a wave P3DH can never have data
for.** Its own docstring already claimed "P3DH only has data from the 2025-06 reference
date onward," but `_reference_dates_since(start_year=2025, ...)` still generated a
2025-03-31 quarterly wave regardless - the code never actually enforced the floor the
docstring described. Added `EARLIEST_P3DH_REFERENCE_DATE = date(2025, 6, 30)` and filtered
on it directly, rather than relying on `start_year` alone.

**Added a second real P3DH template** to `data/modules.txt`: `K_64.01 - EU LI1 -
Differences between the accounting scope and the scope of prudential consolidation...`,
found via the Template search box (same method as EU KM1). Directly relevant to the
spike's still-open Cause 1 question - though, consistent with the Pillar 3 PDF version
already checked there, this is a balance-sheet-only template by regulation (EU
2021/637's own Annex defines it that way), so it won't resolve the income-statement
question even once P3DH has FY2024 data, which it doesn't anyway (see the first
2026-10-06 entry above).

**Scoped `run_update.py` to the actual pilot sample.** It was iterating all 64
discovered entities, not the 37 the project actually trimmed to (task 1.2) - changed the
default to filter on `sp50_2026_rank`, with `--all-entities` to opt back into the full
64 and `--limit N` for a bounded test pass (both added as real, justified CLI options,
not test-only hacks).

**First real test pass** (`--limit 2`, Societe Generale + Deutsche Bank, 2 templates x 8
waves = 32 attempts, ~16 minutes): 12 successes, 20 failures, both failure types genuine
and diagnosable, not scraper breakage:

- **All 16 Societe Generale attempts failed** - not a bug. Searched P3DH's own Entity
  list directly for "Societe" and "Generale": the only match is "Societe Generale Bank -
  Cyprus Ltd", a subsidiary. The parent group entity this project tracks
  (`O2RNE8IBXP4R0TD8PU41`, GLEIF legal name "SOCIETE GENERALE") is **not in P3DH's entity
  list under any name containing "Societe" or "Generale"** - confirmed by direct search,
  not inferred from the failure alone. This is the third independent gap found for this
  specific bank today (also missing its FY2024 ESEF filing - see the ESEF entry above);
  worth deciding later whether Societe Generale is even a workable pilot bank for P3DH
  specifically, or whether its disclosures are filed under a legal entity this project
  hasn't identified yet.
- **4 of Deutsche Bank's LI1 attempts failed, all four at pure-quarterly-only reference
  dates** (2025-06-30-quarterly, 2025-09-30-quarterly, 2026-03-31-quarterly - note
  2025-06-30 ALSO has a semi_annual wave for the same date, and that one succeeded).
  Consistent explanation, not yet independently confirmed beyond this pattern: EU Pillar 3
  disclosure frequency rules (CRR Article 433) require LI1-type disclosures less often than
  core capital metrics like KM1 - KM1 succeeded at every wave/date tested, LI1 only at
  semi-annual/annual ones. Power BI's own ReferenceDate cross-filter narrows to dates that
  actually have data once Template is set, which is what produced this clean a pattern.

**A real inefficiency found and fixed, not just documented**: multiple wave *types* share
the same reference date (31 Dec is quarterly, semi_annual, year_end, AND
year_end_remuneration simultaneously) - but P3DH's export doesn't vary by wave type, only
by the actual date. Before the fix, `run_update.py` fetched the identical data up to 4
times for one date (confirmed: only 5 distinct files existed on disk despite 12
successes, because the output filename - entity+template+date, no wave-type component -
silently overwrote itself on each redundant re-fetch). Fixed by caching this run's own
per-(entity, reference_date, module) result and reusing it across wave types that share a
date, instead of re-driving the browser each time - cuts live fetches roughly 2-4x for
year-end dates without changing the state file's schema or per-wave auditability.

**Dedup fix confirmed, not just reasoned about**: cleared the state file and re-ran with
`--limit 1` (which, in `entities.csv`'s row order, is Societe Generale alone - 16
combinations, 12 of them genuinely unique `(lei, reference_date, module)` keys and 4
sharing a date with another wave type). All 16 wave-keys ended up populated in
`download_log.json` (the schema is unchanged - still one entry per wave), but the run
only took ~2.5 minutes for what would otherwise be 16 full live attempts - consistent
with roughly 12 real attempts plus 4 reused results, not 16 of each.

Sources checked (this update):
- `data/state/download_log.json` after both real runs, read directly to see actual
  success/failure counts, error text, and (after the fix) entry count vs. live-attempt
  count per (entity, wave, module) combination
- Live P3DH Entity search for "Societe"/"Generale" (2 separate queries) to confirm the
  Societe Generale gap rather than assume the failure meant something else
- `data/raw/*.xlsx` file listing, to notice the file-count-vs-success-count mismatch that
  led to finding the wave-type/reference-date redundancy
