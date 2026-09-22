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

### Requirement: Flag non-comparable figures instead of combining them
The package SHALL NOT silently combine two reported figures into a common
metric when they cannot be established as economically comparable.

#### Scenario: Two figures cannot be established as economically equivalent
- **GIVEN** two reported figures relevant to the same requested concept that
  cannot be established as economically equivalent (e.g. a scenario-projected
  stress-test figure vs. a reported actual)
- **WHEN** the package would otherwise combine them into a single value
- **THEN** it instead reports them as non-comparable, together with the reason
  where available, and does not combine them

### Requirement: Coverage is a defined, non-exhaustive set
The package SHALL support a defined set of pilot banks and a defined set of
financial/regulatory variables for v1, and SHALL NOT claim comprehensive
coverage of all European banks or all financial/regulatory variables.

#### Scenario: Unsupported bank or variable requested
- **GIVEN** a bank or variable outside the defined v1 coverage
- **WHEN** the package is called with it
- **THEN** it reports clearly that the bank or variable is unsupported, rather
  than returning an empty or misleading result
