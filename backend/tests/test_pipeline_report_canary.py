"""Tests for report formatting, run row, and the dead-man canary."""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas" / "content_pipeline"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas" / "pipeline_canary"))

from report import format_email, save_run_row  # noqa: E402
from schemas import Source, SourceVerdict  # noqa: E402
from stages import RunState  # noqa: E402
from canary import latest_run_age_hours  # noqa: E402

TODAY = date(2026, 7, 20)


def _state(**kw) -> RunState:
    defaults = dict(pipeline="oplevelser", today=TODAY, season="summer", model_id="m")
    return RunState(**{**defaults, **kw})


def test_email_no_changes():
    subject, body = format_email(_state())
    assert subject == "[aalumvej26] oplevelser: no changes"
    assert "No content changes." in body
    assert "CRAWL STATS" in body and "CONTENT STATUS" in body


def test_email_full_sections():
    state = _state()
    state.published = [{"id": "1", "title": "Koncert", "category": "kultur",
                        "date": "1. august 2026", "domain": "a.dk"}]
    state.archived = [{"id": "2", "title": "Gammel fest", "event_end": "2026-07-01"}]
    state.new_sources = [Source(domain="ny.dk", name="Ny", url="https://ny.dk", tier=2,
                                notes="Events for Thy", status="probation")]
    state.suggested_sources = [SourceVerdict(domain="maaske.dk", relevant=True,
                                             confidence="medium", tier=2,
                                             reasoning="Uncertain freshness")]
    state.retired_sources = ["dead.dk (4 consecutive failed runs)"]
    state.notes = ["Something noteworthy."]
    subject, body = format_email(state)
    assert subject == "[aalumvej26] oplevelser: 1 new, 1 archived, 1 new sources"
    for section in ("PUBLISHED (1)", "ARCHIVED (1)", "NEW SOURCES (1", "SUGGESTED SOURCES (1",
                    "RETIRED SOURCES (1)", "NOTES"):
        assert section in body, section
    assert "maaske.dk (medium)" in body


def test_email_failure_marks_subject_and_body():
    state = _state()
    state.error = "ValidationError: boom"
    subject, body = format_email(state)
    assert "FAILED" in subject
    assert "RUN FAILED" in body and "partial" in body


def test_save_run_row_shape():
    state = _state()
    state.notes = ["a", "b"]
    table = MagicMock()
    save_run_row(state, table)
    item = table.put_item.call_args.kwargs["Item"]
    assert item["pk"] == "PIPELINE_RUN"
    assert item["sk"].startswith("oplevelser#")
    assert item["run_id"] == state.run_id
    assert item["notes"] == "a\nb"
    assert item["error"] == ""


NOW = datetime(2026, 7, 20, 6, 0, tzinfo=timezone.utc)


def test_canary_age_fresh_and_stale():
    fresh = [{"timestamp": "2026-07-20T01:00:00+00:00"}]
    assert latest_run_age_hours(fresh, NOW) == 5.0
    stale = [{"timestamp": "2026-07-01T00:00:00+00:00"}]
    assert latest_run_age_hours(stale, NOW) > 24


def test_canary_no_rows_or_bad_timestamp():
    assert latest_run_age_hours([], NOW) is None
    assert latest_run_age_hours([{"timestamp": "garbage"}], NOW) is None


def test_canary_picks_newest():
    items = [{"timestamp": "2026-07-01T00:00:00+00:00"},
             {"timestamp": "2026-07-20T05:00:00+00:00"}]
    assert latest_run_age_hours(items, NOW) == 1.0
