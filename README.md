# European Bank Financial Data Reconciliation

1. The demo

At this point the project reads better as an interactive dashboard than as a bare package call, so that's how it's demoed: open the dashboard, build a basket of up to 6 banks by clicking logos on a map of Europe, pick which financial and regulatory concepts to compare — including several standardized as a percentage of total assets or of total RWA where that's a meaningful ratio (e.g. net fee income or profit for the year against assets; Tier 1 capital, total capital, or an RWA-breakdown item against RWA) — and get a results table across the selected banks, with missing data shown as a dash with its real reason on hover, the best value per ratio row highlighted, and a timestamped CSV export. Every figure in that table is produced by calling the real package functions (`get_financial_data()`, `compute_rwa_density()`, `compute_cost_to_income_ratio()`) exactly as shipped, precomputed offline so the dashboard needs no live backend — nothing shown there is reimplemented or simplified for presentation.

The underlying package interface this dashboard is built on still works exactly as originally pitched: I can install the Python package and run a function for a bank and reporting period directly, and get back a table with the same figures, source items, and provenance the dashboard uses. A reviewable snapshot of that direct function-call output for the MVP's pilot bank (Erste Group Bank AG, EBA Stress Test 2025 + its own ESEF filing) is published at <https://esst-prog2.github.io/Bank_Data/review.html> (source: `docs/review.html`); a second snapshot shows the same function run for two banks side by side (Erste Group Bank AG + BNP Paribas) at <https://esst-prog2.github.io/Bank_Data/compare.html> (source: `docs/compare.html`).

2. The shape
in          a bank identifier, reporting period, and requested financial or
            regulatory concepts

out         a pandas DataFrame containing the requested data, together with
            source and provenance information

in between  retrieve data from machine-readable bank and regulatory reports;
            map source-specific reporting items to standardized concepts;
            tag each figure with its source and provenance (e.g. reported
            actual vs. scenario-projected) so it can be checked against the
            publication it came from, rather than reconciled into a single
            cross-source value

3. The size
First useful version

Retrieve a defined set of financial-statement and regulatory data for a supported European bank with data available through ESEF, this term.
Return the data in a consistent pandas DataFrame structure.
Support requests for a bank, reporting period, and selected variables.
Map returned variables to their underlying source reporting items.
Provide enough metadata (source reporting item, standardized concept, and provenance — reported actual vs. scenario-projected) to check each figure against the source it came from.
Distinguish data that is missing from the source from data that could not be retrieved or processed by the package.
Allow the returned data to be used in further calculations.

Not this term
Comprehensive coverage of every European bank.
Coverage of banks whose data isn't available through ESEF — a this-term scope boundary set by ESEF's own EU Transparency Directive coverage (issuers with securities on an EU regulated market), not a permanent limitation of this package.
Comprehensive coverage of every financial and regulatory variable.
A public API or hosted service.
Advanced statistical modelling based on the retrieved data.
Normalizing or reconciling figures across different accounting standards or reporting frameworks into a single comparable value.

*Note, 2026-11-01: this boundary turned out not to hold for "a standalone dashboard or web application" or "extensive financial analysis and visualization." Seeing how much more the project's point came across as an interactive dashboard than as a bare function call, one was built directly on top of the package described in section 2 — calling its functions exactly as shipped, not reimplementing anything — and became the actual demo in section 1. Everything else in this list still stands.*

4. How we would know it works

Given a supported bank, reporting period, and available variable, the package returns the corresponding value together with its source reporting item and standardized concept mapping.
Given a requested variable that is genuinely absent from the underlying source, the package identifies the data as missing from the source rather than presenting it as a retrieval or processing failure.
Given a returned figure, the package identifies its source reporting item, standardized concept, and provenance (reported actual vs. scenario-projected) well enough to check it against the publication it came from.
Given the same concept reported by more than one source for a bank and period, the package returns each source's figure tagged by provenance rather than combining them into a single value.

5. What could stop this

The project depends on the availability and stability of machine-readable reporting data published by European banks and regulatory institutions.

Potential risks include:

changes in the structure or taxonomy of XBRL/ESEF reports;
incomplete or inconsistent machine-readable disclosures;
changes to regulatory reporting formats;
difficulty obtaining or processing bulk regulatory reporting data.

By design, the project does not attempt to reconcile figures across different accounting standards, consolidation scopes, or reporting frameworks into a single comparable value — that is a much larger research problem than this project takes on. Instead, every returned figure carries enough source and provenance metadata (including whether it is a reported actual or a scenario-projected figure) to be checked against the publication it came from. Within-bank traceability, across a given bank's own periods and sources, takes priority over comparability with an arbitrary third party.

The main technical and conceptual risk that remains is the mapping between source-specific reporting items and standardized concepts: similar-looking variables do not necessarily represent the same underlying reporting item, and the same concept may be reported using different items across banks or reporting frameworks.

The primary data sources will be publicly available machine-readable financial reports and regulatory disclosures. The project will use data that can legally be downloaded and processed, and a small sample of the source data will be included or referenced for reproducible testing and demonstration.
