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
