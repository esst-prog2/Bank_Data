# European Bank Financial Data Reconciliation

1. The demo

I install the Python package and run a function for two European banks and a selected reporting period. It returns a table containing financial-statement and regulatory metrics for that bank and period, including the underlying source item for each figure. I can inspect the mapping to see which XBRL/ESEF or regulatory reporting item produced each value, what standardized concept it represents, and whether it is a reported actual or a scenario-projected figure (e.g. from an EU-wide stress test). Every figure carries enough metadata to check it against the publication it came from; the package does not attempt to reconcile figures across different accounting standards or reporting frameworks into a single comparable value — if the same concept is reported by more than one source, it returns each one tagged by its provenance rather than picking or combining them. I can then use the returned data directly in Python to calculate a metric such as RWA density.

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

Retrieve a defined set of financial-statement and regulatory data for a supported European bank.
Return the data in a consistent pandas DataFrame structure.
Support requests for a bank, reporting period, and selected variables.
Map returned variables to their underlying source reporting items.
Provide enough metadata (source reporting item, standardized concept, and provenance — reported actual vs. scenario-projected) to check each figure against the source it came from.
Distinguish data that is missing from the source from data that could not be retrieved or processed by the package.
Allow the returned data to be used in further calculations.

Not this term
Comprehensive coverage of every European bank.
Comprehensive coverage of every financial and regulatory variable.
A standalone dashboard or web application.
A public API or hosted service.
Extensive financial analysis and visualization.
Advanced statistical modelling based on the retrieved data.
Normalizing or reconciling figures across different accounting standards or reporting frameworks into a single comparable value.

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
