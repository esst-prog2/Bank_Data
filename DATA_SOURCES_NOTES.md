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
