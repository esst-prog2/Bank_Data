"""The script you schedule (Windows Task Scheduler / cron) to keep local data current.

What it does each run:
    1. load the tracked entities (data/entities.csv)
    2. compute every wave that could plausibly be published by now (waves.py)
    3. skip anything already recorded as done in data/state/download_log.json
    4. attempt the rest via edap_downloader.fetch_module()
    5. record success/failure for each attempt, so next run only retries failures/new waves

This is intentionally idempotent and safe to run as often as you like (e.g. daily) - it will
mostly no-op between real EBA publication waves. `edap_downloader.fetch_module()` is real as
of 2026-10-06 (Playwright-driven, verified against the live P3DH page - see that module's
and `edap_scraper.py`'s docstrings), so a run now genuinely attempts each entity/wave/item
combination rather than failing all of them by design.

**`data/modules.txt`'s format changed 2026-10-06**: despite the name (kept for now - see
`edap_downloader.py`'s docstring for why), each line is P3DH's exact **Template** option
text (e.g. "K_61.00 - EU KM1 - Key metrics template"), not a short module code like "CODIS"
or "FINDIS" - the live investigation found P3DH's own Module filter is fully cross-filtered
from Template and doesn't need to be set independently, so tracking short module codes here
was never going to be enough to identify one specific table anyway. Get the exact template
strings from the Data Points Report's own "Template" filter (verified working via
`edap_scraper.py` - search box included) - a dropdown with ~100+ entries covering every
EU-template code, not just the ones used in `reconcile.py` so far.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeoutError

from data_acquisition import waves
from data_acquisition.edap_downloader import BulkAccessNotConfirmed, fetch_module
from data_acquisition.entities import load_entities

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent
_STATE_FILE = _ROOT / "data" / "state" / "download_log.json"
_MODULES_FILE = _ROOT / "data" / "modules.txt"
_RAW_DIR = _ROOT / "data" / "raw"


def _classify_failure(exc: Exception, wave: "waves.Wave") -> tuple[str, int | None]:
    """Buckets a fetch_module() failure by its actual cause instead of the generic
    "failed" every exception collapsed into before (task 1.4) - a live full-pilot run
    already produced each of these for real, not just the EBA-calendar case the task
    was originally written for:

      - config_missing_entity: `lei` isn't in entities.csv at all (BulkAccessNotConfirmed) -
        a tracking gap on our side, not a P3DH fact.
      - entity_not_found_on_p3dh: the Entity slicer has no matching option - this bank
        genuinely isn't (yet, or ever) on P3DH, or its name doesn't match (see
        edap_scraper.py's entity-matching docstring).
      - template_or_date_not_available: the Template or Reference date slicer had no
        matching option for this entity. Deliberately NOT split further into "not yet
        published" vs. "this entity/template doesn't disclose at this frequency" -
        both produce the identical missing-option symptom and there's no reliable way
        to tell them apart from the error alone (same limitation esef_client.find_filing's
        docstring documents for its own tie-break: metadata isn't enough, only checking
        an adjacent period's own data is certain). `days_overdue` (how long this wave's
        deadline has already passed) is returned instead, as a hint a human can use: a
        wave barely past deadline is more likely still pending; one months overdue is
        more likely a genuine frequency/template mismatch.
      - scraper_error: anything else - a real page/network break (iframe, export button,
        download timeout) unrelated to any slicer not finding its value. This is the only
        bucket that should alarm an operator; the other three are expected, routine outcomes.
    """
    if isinstance(exc, BulkAccessNotConfirmed):
        return "config_missing_entity", None
    msg = str(exc)
    if isinstance(exc, PWTimeoutError) and "slicer 'entity'" in msg:
        return "entity_not_found_on_p3dh", None
    if isinstance(exc, PWTimeoutError) and ("slicer 'template'" in msg or "slicer 'reference_date'" in msg):
        days_overdue = (date.today() - wave.earliest_expected_publication).days
        return "template_or_date_not_available", days_overdue
    return "scraper_error", None


def _load_state() -> dict:
    if _STATE_FILE.exists():
        return json.loads(_STATE_FILE.read_text())
    return {}


def _save_state(state: dict) -> None:
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def _load_modules() -> list[str]:
    if not _MODULES_FILE.exists():
        raise FileNotFoundError(
            f"{_MODULES_FILE} not found - create it with one exact P3DH Template option "
            "per line (e.g. \"K_61.00 - EU KM1 - Key metrics template\"), not a short "
            "module code - see this script's module docstring for why. Check the Data "
            "Points Report's own 'Template' filter for the exact text."
        )
    return [line.strip() for line in _MODULES_FILE.read_text().splitlines() if line.strip()]


def main(pilot_only: bool = True, limit: int | None = None) -> None:
    """`pilot_only=True` (the default) restricts the run to entities with a non-empty
    `sp50_2026_rank` in entities.csv - the 37-bank sample task 1.2 actually trimmed to,
    not the full 64-bank discovery universe `eba_exercises.py` happened to surface. Each
    attempt drives a real headless browser against the live P3DH page (~15-30s each,
    longer on failure), so a full pass (pilot_only entities x all waves x all templates)
    is real wall-clock time, not an instant bulk download - `limit` caps how many
    entities are attempted, for a bounded test pass rather than the whole pilot sample."""
    entities = load_entities()
    if pilot_only:
        entities = [e for e in entities if e.sp50_2026_rank]
    if limit is not None:
        entities = entities[:limit]
    modules = _load_modules()
    pending_waves = waves.expected_waves()
    state = _load_state()

    log.info("%d entities x %d modules x %d waves = %d combinations to check",
              len(entities), len(modules), len(pending_waves),
              len(entities) * len(modules) * len(pending_waves))

    new_successes = new_failures = skipped = 0
    # Several waves can share the same reference_date (e.g. 31 Dec is simultaneously
    # quarterly/semi_annual/year_end/year_end_remuneration), and P3DH's own export doesn't
    # vary by OUR wave-type label - only by entity/template/reference_date. Without this,
    # a live run repeats the exact same browser-driven fetch once per wave type sharing a
    # date (confirmed: 4x redundant fetches for one date in an initial test run) - cache
    # this run's own results per (lei, reference_date, module) and reuse them across waves
    # that share a date, instead of re-fetching.
    # Save after every entity, not just once at the end - confirmed necessary 2026-10-06:
    # a ~3-hour real run was killed mid-pass (the machine slept/restarted overnight) and
    # lost every bit of its state because nothing had been written to disk yet, even
    # though ~20 entities' worth of real files had already been downloaded successfully.
    this_run_by_date: dict[tuple[str, str, str], dict] = {}
    for entity in entities:
        for wave in pending_waves:
            for module in modules:
                key = f"{entity.lei}|{wave.wave_id}|{module}"
                if state.get(key, {}).get("status") == "success":
                    skipped += 1
                    continue
                date_key = (entity.lei, wave.reference_date.isoformat(), module)
                if date_key in this_run_by_date:
                    state[key] = this_run_by_date[date_key]
                    if state[key]["status"] == "success":
                        new_successes += 1
                    else:
                        new_failures += 1
                    continue
                try:
                    result = fetch_module(entity.lei, wave.reference_date, module, _RAW_DIR)
                    state[key] = {
                        "status": "success",
                        "file": str(result.file_path),
                        "source": result.source,
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                    }
                    new_successes += 1
                except Exception as exc:  # noqa: BLE001 - we want every failure recorded
                    failure_type, days_overdue = _classify_failure(exc, wave)
                    state[key] = {
                        "status": "failed",
                        "failure_type": failure_type,
                        "days_overdue": days_overdue,
                        "error": str(exc),
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                    }
                    new_failures += 1
                this_run_by_date[date_key] = state[key]
        _save_state(state)  # persist after each entity - see comment above the loop

    log.info("done: %d new successes, %d new failures, %d already-had skipped",
              new_successes, new_failures, skipped)
    failure_types: dict[str, int] = {}
    for entry in state.values():
        if entry.get("status") == "failed":
            failure_types[entry.get("failure_type", "unclassified")] = (
                failure_types.get(entry.get("failure_type", "unclassified"), 0) + 1
            )
    if failure_types:
        log.info("failures by type (all-time, not just this run): %s", failure_types)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all-entities", action="store_true",
                         help="check every discovered LEI in entities.csv, not just the sp50_2026_rank pilot sample")
    parser.add_argument("--limit", type=int, default=None,
                         help="only attempt the first N entities - for a bounded test pass")
    args = parser.parse_args()
    main(pilot_only=not args.all_entities, limit=args.limit)
