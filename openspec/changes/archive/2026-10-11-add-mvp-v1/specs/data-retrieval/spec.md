# data-retrieval (delta)

## ADDED Requirements

### Requirement: Retrieve requested variables for a supported bank and period
The package SHALL, given a bank identifier, a reporting period, and one or more
requested financial-statement or regulatory concepts, return a pandas DataFrame
containing the requested values for that bank and period.

#### Scenario: Supported bank, period, and available variable
- **GIVEN** a supported bank, a reporting period, and a variable available from
  that bank's underlying source for that period
- **WHEN** the package is called with that bank, period, and variable
- **THEN** it returns the corresponding value together with its source
  reporting item and its standardized-concept mapping

### Requirement: Distinguish missing-from-source from retrieval/processing failure
The package SHALL distinguish a variable that is genuinely absent from the
underlying source from a variable that could not be retrieved or processed by
the package.

#### Scenario: Variable genuinely absent from source
- **GIVEN** a requested variable that the source does not report for that bank
  and period
- **WHEN** the package processes the request
- **THEN** it identifies the data as missing from the source, and does not
  present it as a retrieval or processing failure

#### Scenario: Retrieval or processing failure
- **GIVEN** a requested variable that the source would report, but retrieval or
  processing of it fails (e.g. a source outage, an unrecognized reporting item)
- **WHEN** the package processes the request
- **THEN** it raises or reports the failure explicitly rather than returning it
  as missing or silently omitting it

### Requirement: Every returned figure is falsifiable against its source
The package SHALL tag every returned figure with enough source and
provenance metadata — including whether it is a reported actual or a
scenario-projected figure (e.g. an EU-wide stress test) — that the figure
can be checked against the original publication it came from. The package
SHALL NOT attempt to establish or assert economic equivalence between
figures from different accounting standards, consolidation scopes, or
reporting frameworks. Within-bank traceability across that bank's own
periods and sources takes priority over normalizing figures for comparison
against other banks or external standards.

#### Scenario: Reported actual vs. scenario-projected figure for the same concept
- **GIVEN** two figures for the same standardized concept and bank, one from
  a reported-actuals source (Pillar 3 / ESEF) and one from a stress-test
  scenario projection
- **WHEN** the package returns both
- **THEN** each is tagged with its provenance (reported_actual /
  scenario_projection) and neither is combined into a single value or
  presented as interchangeable

#### Scenario: Figure traceable to its origin
- **GIVEN** any returned figure
- **WHEN** its correctness is checked
- **THEN** the package's output identifies the exact source publication,
  exercise (if applicable), and reporting item the figure came from,
  sufficient to verify it independently against that source

#### Scenario: Multiple sources report the same concept
- **GIVEN** a bank/period/concept for which more than one wired-up source
  reports a figure
- **WHEN** the package returns results for that request
- **THEN** it returns each source's figure tagged by its provenance, rather
  than reconciling them into a single authoritative value

### Requirement: Coverage is a defined, non-exhaustive set
The package SHALL support a defined set of pilot banks and a defined set of
financial/regulatory variables for v1, and SHALL NOT claim comprehensive
coverage of all European banks or all financial/regulatory variables.

#### Scenario: Unsupported bank or variable requested
- **GIVEN** a bank or variable outside the defined v1 coverage
- **WHEN** the package is called with it
- **THEN** it reports clearly that the bank or variable is unsupported, rather
  than returning an empty or misleading result
