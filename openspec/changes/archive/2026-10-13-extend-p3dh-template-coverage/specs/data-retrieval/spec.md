# Spec Delta

## ADDED Requirements

### Requirement: Concept mapping is curated per fixed source item, never inferred from per-filer vocabulary
The package SHALL map a source item to a standardized concept only when that
item is identified the same, bank-independent way across every filer (e.g. a
fixed regulatory template row/item code). The package SHALL NOT map a
concept by inferring or guessing a correspondence from a breakdown label
that a filer chooses for itself (e.g. its own chart-of-accounts wording),
even when that same label happens to work for one bank.

#### Scenario: Source item identified by a fixed, bank-independent code
- **GIVEN** a source template whose items are identified by a regulatory
  code that means the same thing for every filer
- **WHEN** the package maps that item to a standardized concept
- **THEN** every bank's figure for that item is returned under the same
  standardized concept, using the same mapping

#### Scenario: Source item identified only by a filer-chosen label
- **GIVEN** a source template whose items are identified by a label each
  filer chooses for its own reporting categories, not a shared code
- **WHEN** the package decides whether to map one of those labels to a
  standardized concept
- **THEN** it does so only for a label the template itself designates as a
  defined total, and never by matching or guessing a correspondence between
  two filers' differently-worded categories

#### Scenario: A mapped filer-chosen label is absent from one bank's own report
- **GIVEN** a standardized concept mapped from a filer-chosen label that is
  present in some filers' reports but not a specific bank's own report for
  that period
- **WHEN** the package is asked for that concept for that bank and period
- **THEN** it reports the value as missing from source for that bank, never
  as a retrieval/processing failure, and never by substituting a value from
  a differently-labeled category in that bank's own report
