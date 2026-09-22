"""The script you schedule (Windows Task Scheduler / cron) to keep local data current.

What it does each run:
    1. load the tracked entities (data/entities.csv)
    2. compute every wave that could plausibly be published by now (waves.py)
    3. skip anything already recorded as done in data/state/download_log.json
    4. attempt the rest via edap_downloader.fetch_module()
    5. record success/failure for each attempt, so next run only retries failures/new waves

This is intentionally idempotent and safe to run as often as you like (e.g. daily) - it will
mostly no-op between real EBA publication waves. Nothing here downloads anything until
edap_downloader.fetch_module() is actually implemented (see that module's docstring); until
then this script will run, find "new" work every time, fail loudly on each item, and log the
failures - which is the intended behaviour, not a bug, so the gap is visible rather than
silently masked.

Modules to request per entity/period are not hardcoded here on purpose - the EBA guide lists
~10 disclosure modules (CODIS, FINDIS, ESGDIS among them) but we could not confirm the full,
authoritative list of module codes from public sources; pull the exact list your entities
actually submit from the Data Points Report's own "Module" filter and put it in
data/modules.txt (one code per line) before running this for real.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from data_acquisition import waves
from data_acquisition.edap_downloader import fetch_module
from data_acquisition.entities import load_entities

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent
_STATE_FILE = _ROOT / "data" / "state" / "download_log.json"
_MODULES_FILE = _ROOT / "data" / "modules.txt"
_RAW_DIR = _ROOT / "data" / "raw"


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
            f"{_MODULES_FILE} not found - create it with one disclosure-module code per "
            "line (check the 'Module' filter on the Data Points Report page for the exact "
            "codes your tracked entities actually submit)."
        )
    return [line.strip() for line in _MODULES_FILE.read_text().splitlines() if line.strip()]


def main() -> None:
    entities = load_entities()
    modules = _load_modules()
    pending_waves = waves.expected_waves()
    state = _load_state()

    log.info("%d entities x %d modules x %d waves = %d combinations to check",
              len(entities), len(modules), len(pending_waves),
              len(entities) * len(modules) * len(pending_waves))

    new_successes = new_failures = skipped = 0
    for entity in entities:
        for wave in pending_waves:
            for module in modules:
                key = f"{entity.lei}|{wave.wave_id}|{module}"
                if state.get(key, {}).get("status") == "success":
                    skipped += 1
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
                    state[key] = {
                        "status": "failed",
                        "error": str(exc),
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                    }
                    new_failures += 1

    _save_state(state)
    log.info("done: %d new successes, %d new failures, %d already-had skipped",
              new_successes, new_failures, skipped)


if __name__ == "__main__":
    main()
