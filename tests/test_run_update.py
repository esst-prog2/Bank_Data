"""Tests for data_acquisition.run_update._classify_failure (task 1.4): every failure
collapsed into the same generic status: "failed" before this - these tests pin down
the four real, distinct causes a live pilot run actually produced, using the exact
exception shapes `fetch_module()` and `edap_scraper._select_slicer()` raise.
"""

from __future__ import annotations

from datetime import date

import pytest
from playwright.sync_api import TimeoutError as PWTimeoutError

from data_acquisition import waves
from data_acquisition.edap_downloader import BulkAccessNotConfirmed
from data_acquisition.run_update import _classify_failure

_WAVE = waves.Wave(date(2025, 6, 30), waves.ReferenceDateType.QUARTERLY, date(2025, 10, 30))


def test_missing_entity_config_is_distinguished_from_scraper_failure():
    failure_type, days_overdue = _classify_failure(BulkAccessNotConfirmed("lei not tracked"), _WAVE)
    assert failure_type == "config_missing_entity"
    assert days_overdue is None


def test_entity_slicer_miss_means_not_on_p3dh():
    exc = PWTimeoutError("Could not set slicer 'entity' to 'Some Bank AG': timeout")
    failure_type, days_overdue = _classify_failure(exc, _WAVE)
    assert failure_type == "entity_not_found_on_p3dh"
    assert days_overdue is None


@pytest.mark.parametrize("field", ["template", "reference_date"])
def test_template_or_date_slicer_miss_reports_days_overdue(field):
    exc = PWTimeoutError(f"Could not set slicer '{field}' to 'X': timeout")
    failure_type, days_overdue = _classify_failure(exc, _WAVE)
    assert failure_type == "template_or_date_not_available"
    assert days_overdue == (date.today() - _WAVE.earliest_expected_publication).days


def test_unrelated_timeout_is_a_real_scraper_error_not_a_routine_gap():
    exc = PWTimeoutError("Timeout waiting for selector iframe.powerbi-frame")
    failure_type, days_overdue = _classify_failure(exc, _WAVE)
    assert failure_type == "scraper_error"
    assert days_overdue is None
