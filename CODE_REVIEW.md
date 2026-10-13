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
