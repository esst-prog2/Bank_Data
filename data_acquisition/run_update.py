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
            f"{_MODULES_FILE} not found - create it with one exact P3DH Template option "
            "per line (e.g. \"K_61.00 - EU KM1 - Key metrics template\"), not a short "
            "module code - see this script's module docstring for why. Check the Data "
            "Points Report's own 'Template' filter for the exact text."
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
