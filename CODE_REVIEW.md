# Homework 6 — whole-codebase review log

One section per specialised review (Session 6 slides' list), each landed in its own
commit on the `hw6-code-review` branch. Written as the review happens, not
backfilled - a review that finds nothing actionable is recorded as such, not
skipped, since "I looked and it's clean" is itself a real result.

## 1. Spec drift (code vs. `openspec/specs/data-retrieval/spec.md`)

Checked `reconcile.py` and `run_update.py` against every requirement/scenario in
the live spec, and the spec/README against what's actually built.

**Found:** three stale pointers to `openspec/changes/add-mvp-v1/...`, a path that
stopped existing when that change was implemented and archived to
`openspec/changes/archive/2026-10-11-add-mvp-v1/` (the live spec moved to
`openspec/specs/data-retrieval/spec.md`): `reconcile.py`'s module docstring,
`test_reconcile.py`'s module docstring, and `openspec/specs/README.md` (which
also still claimed "nothing has been archived yet" - false, two changes have
been archived). No requirement itself was unimplemented or undocumented-but-built.

**Fixed:** updated all three to point at the live spec location; rewrote
`openspec/specs/README.md`'s second paragraph to describe what's actually there.
No behavior change. Commit `2a45eb7`.

## 2. Unchosen names (functions/concepts invented with no spec/conversation origin)

Read every module in `data_acquisition/` end to end looking for a name - a
function, parameter, or constant - that isn't traceable to a spec requirement, a
dated decision in `PLANNING_LOG.md`, or a documented, checked finding in
`DATA_SOURCES_NOTES.md`.

**Found:** nothing matching the slide's `apply_slack_buffer`-style pattern (an
abstraction the agent decided was needed and quietly built). Every non-obvious
name in this codebase - `_distinctive_words`, `_search_candidates`,
`_classify_failure`'s four failure-type buckets, `_P3DH_RATIO_CONCEPTS`, EU LI1's
"Open Key" match field - carries a docstring or inline comment tying it to a
specific confirmed bug, a specific regulatory template's real structure, or a
dated user decision. This project's existing convention (append-only
`PLANNING_LOG.md`/`DATA_SOURCES_NOTES.md`, "decided by user" vs. "decided by
agent" tags on every entry) appears to have substantially prevented this failure
mode rather than just making it easier to catch after the fact.

One adjacent, real issue surfaced while reading `eba_exercises.py` against
`entities.py` - not an invented name, but a genuine correctness bug from schema
drift between two modules. Logged and fixed under review 3 instead (it's a
"patched where it broke, not where it's wrong"-shaped problem: the entities.csv
schema grew in `entities.py` without `eba_exercises.py`'s writer being updated to
match), not a naming one.

**Fixed:** nothing in this review - no findings to act on.

## 3. Patched where it broke, not where it's wrong (symptom patches vs. root-cause fixes)

Read the full commit history on `main` (34 commits) looking for the slide's pattern:
an assumption that's wrong from commit 1, with each later commit patching the next
symptom it causes instead of revisiting the assumption itself.

**Found:** no such chain in the history - every "fix" commit (`93e90be`, `ea88a7a`,
`c8d86db`) is a single, root-cause fix for a separately investigated bug, confirmed
against real data before being trusted (matches this project's established
discipline of checking a 2-bank finding against the full sample before relying on
it, e.g. the EU LI1 sparsity re-check in `PLANNING_LOG.md`'s 2026-10-13 entries).

Comparing modules against each other instead of against history surfaced a
same-shaped problem, though: `data_acquisition/entities.py`'s `Entity` dataclass and
`data/entities.csv` grew two columns (`sp50_2026_rank`, `pilot_added`) on
2026-10-11, but `eba_exercises.py`'s `build_entities_csv()` - which reads and
rewrites that same CSV - was never updated to match. It hardcoded
`fieldnames=["lei", "name", "country", "notes"]`; calling it again against the
*current* entities.csv would read rows carrying the two newer keys and then crash
in `csv.DictWriter.writerow()` (`ValueError`, default `extrasaction='raise'`) on
the first row, silently destroying nothing (it fails before writing) but making the
function completely unusable without anyone having noticed, since nothing calls it
in the normal run_update.py workflow. Same root cause as the slide's pattern - one
part of the code changed without revisiting an assumption a different part of the
code depended on - just surfacing as an unmaintained function instead of a chain of
commits.

**Fixed:** `build_entities_csv()` now reads the existing file's own header as its
fieldnames (falling back to the 4 base columns only when there's no existing file),
so it preserves whatever columns `entities.csv` actually has instead of hardcoding
a stale list. Added `tests/test_eba_exercises.py` - a regression test against a
6-column entities.csv (the real current shape) that would have failed with the old
code's `ValueError`.

## 4. Duplicate modules (a copy instead of a change)

Checked for two modules/functions doing nearly the same job under different names:
compared every `data_acquisition/*.py` file pairwise for overlapping responsibility,
hashed every `.py` file in the repo for byte-identical copies, and checked the three
independent `requests.get`-based clients (`eba_exercises.py`, `esef_client.py`,
`gleif_client.py`) against each other.

**Found:** no duplicate modules. No two files hash identically; the three HTTP
clients each wrap a genuinely different external API with its own error-handling
shape (`GleifError`, `EsefNotFoundError`/`EsefDataError`, bare `requests`
exceptions) rather than reimplementing each other. `edap_downloader.py` vs.
`edap_scraper.py`'s split (swappable interface vs. concrete Playwright
implementation) is deliberate and documented, not an accidental copy.
`spike/compare_sources.py` recomputes RWA density inline rather than calling
`reconcile.compute_rwa_density()`, but not as an accidental duplicate - it computes
the ratio for BOTH `reported_actual` and `restated_actual` TREA side by side (the
spike's whole point), which `compute_rwa_density()` deliberately refuses to do (see
its own docstring); the two aren't interchangeable.

Did find one real staleness issue while comparing modules against each other:
`data_acquisition/__init__.py`'s module list only named 5 of the package's 9
modules - `eba_exercises`, `esef_client`, `edap_scraper`, and `reconcile` (the
package's actual main surface) were all missing, presumably because the docstring
was written early and never revisited as the package grew.

**Fixed:** updated `__init__.py`'s module list to name all 9 modules. No behavior
change.

## 5. Errors that disappear (swallowed exceptions)

Grepped every `except` clause in `data_acquisition/` (14 total) for the slide's
`except Exception: return None`/`except: pass` pattern.

**Found:** 13 of 14 `except` clauses either re-raise as one of this project's own
loud error types (`DataSourceError`, `EsefDataError`, ...) or deliberately
represent a documented "missing from source, not a failure" outcome the spec
itself requires (e.g. `reconcile.py`'s `EsefNotFoundError` -> `missing_from_source`
row). `run_update.py`'s one broad `except Exception` is intentional and already
justified inline (`# noqa: BLE001 - we want every failure recorded`): it still
classifies and persists every failure to the state file rather than discarding it,
matching AGENTS.md's own stated convention ("every acquisition module raises
loudly on failure... run_update.py's per-item try/except records failures in the
state file instead of swallowing them").

One real gap: `eba_exercises.download_full_database()`'s per-file
`except requests.RequestException` skip (a deliberate, documented choice - EBA's
asset server 403s some URLs, and one bad file shouldn't abort the whole batch) only
surfaced via a bare `print()`, with no logger set up in that module at all (unlike
`run_update.py`, which already uses `logging`). A caller invoking this
programmatically rather than watching a terminal would lose every skip silently -
the written-files count would just come back short with no way to tell why.

**Fixed:** added a module logger (matching `run_update.py`'s convention) and
replaced the `print()` with `log.warning(...)`. The skip-and-continue behavior
itself is unchanged - it's correct, not the thing that was swallowed - only its
visibility to a non-interactive caller is.

## 6. Things nobody chose (unchosen dependencies, dead code)

Checked every package `requirements.txt` lists against actual imports (is it
used?), checked actual imports against what's declared (is everything used
actually declared?), and scanned every public and private function/class in
`data_acquisition/` for zero references outside its own definition.

**Found:** every package in `requirements.txt` is genuinely used (no hallucinated
or abandoned entries), and every function/class in the package is referenced at
least once elsewhere (no dead code). But the reverse check caught a real gap:
`tests/test_reconcile.py` imports `pytest` directly, and the whole suite is run
via `python -m pytest` - yet `pytest` was never in `requirements.txt` at all.
Nobody chose to leave it out; it's just a dependency the test suite has always
silently relied on the environment already having. A clean `pip install -r
requirements.txt` followed by `pytest` would fail with `ModuleNotFoundError`.

**Fixed:** added `pytest>=8.0` to `requirements.txt`.

## 7. The quiet default (a missing value silently becomes a decision)

Grepped every `.get(key, default)` call in `data_acquisition/` (24 total) and
checked each one: is the key's absence a real, expected possibility the caller
already handles, or would a missing key actually be a bug masquerading as a
normal case?

**Found:** 23 are reading untrusted external JSON (filings.xbrl.org/GLEIF API
responses) or a state file whose entries may predate a schema field, both genuine
"this key's absence is expected and already handled downstream" cases. One real
quiet default: `eba_exercises.discover_full_database_files()`'s
`_KNOWN_FULL_DATABASE_FILES.get((exercise, year), [])` - if live scraping found
nothing (e.g. EBA redesigned the landing page) AND no hardcoded fallback exists
for that year, this silently returned `[]`. `download_full_database()` would then
just write zero files with no error, and the caller has no way to tell "this
exercise/year genuinely has zero files" (which never actually happens - every
exercise year has some) apart from "both lookup paths failed". The missing key
became a decision - "proceed as if there's nothing to fetch" - nobody actually
made.

**Fixed:** added `ExerciseDataUnavailable`, raised when neither live scraping nor
the fallback list produces anything, instead of returning `[]`. Added
`test_discover_full_database_files_raises_when_nothing_found`.

## 8. Testing gaps (unit vs. integration balance)

Read `tests/test_reconcile.py` and `tests/test_run_update.py` end to end and
classified every test by the slides' own definition: unit (hand-invented, frozen
inputs, checks the logic) vs. integration (the real source, checks the pieces
connect).

**Found:** a real, significant imbalance. `test_run_update.py`'s 5 tests are all
genuine unit tests (hand-built exception objects, no I/O). But every one of
`test_reconcile.py`'s 24 tests calls `get_financial_data()` (or a `compute_*`
wrapper around it) against real cached files under `data/raw/`, and 10 of them
`pytest.skip()` outright when that cache is missing. That's the right call for
checking "do the pieces connect to the real source" - and this project is unusually
careful about pinning expected values to independently-sourced references before
trusting them (e.g. the RWA density test's externally-sourced 44.5%). But it means
**reconcile.py's own processing logic has zero coverage that doesn't depend on a
real cached file being present** - the unit half of the slide's table is empty for
this module. A fresh clone with no `data/` cache runs almost none of
`test_reconcile.py` and still goes green; CI could pass while checking nothing of
`reconcile.py`'s actual parsing/conversion logic.

**Fixed (partial, scoped):** added `tests/test_reconcile_unit.py` - real unit tests
with hand-built, frozen inputs, no cache or network dependency:
- `_read_p3dh_fact`'s happy path and its malformed-export error path, against a
  synthetic `.xlsx` built in `tmp_path`.
- Extracted `_read_p3dh_fact`'s nested `cell()` bounds-checking closure to a
  module-level `_row_cell()` specifically so the real openpyxl row-trimming bug fix
  (2026-10-12) has a direct unit test with a hand-built short tuple - confirmed this
  test fails with `IndexError` on the pre-fix plain-indexing logic, and confirmed
  (while building the fixture) that openpyxl's own writer doesn't actually reproduce
  the real trimming behavior, so a file-based version of this specific test would
  have silently tested nothing.
- `_period_to_esef_period_end`/`_esef_period_end_to_period`'s round-trip and its
  non-December rejection.

This covers the two riskiest, most-recently-buggy pieces of pure logic, not the
whole module - `_stress_test_rows`/`_esef_rows`/`_p3dh_rows`'s branching, the
EUR->EUR-millions conversion, and `get_financial_data()`'s own DataFrame assembly
are still only covered by the integration suite. Flagged, not silently left for
"later" - a fuller unit-test pass for the rest of `reconcile.py`'s logic is real,
scoped follow-up work this review surfaced but didn't attempt to finish in one
commit.
