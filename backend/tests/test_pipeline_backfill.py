"""Tests for the in-Lambda backfill mode: pure plan logic + handler wiring."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas" / "content_pipeline"))

from backfill import ParsedDates, format_report, plan_changes  # noqa: E402

TODAY = date(2026, 7, 20)


def _post(pid: str, status: str = "published", tag: str = "event", **extra) -> dict:
    return {
        "id": pid,
        "sk": f"POST#{pid}",
        "status": status,
        "tag_key": tag,
        "translations": {"da": {"title": f"Post {pid}", "date": "x"}},
        **extra,
    }


def _parsed(pid: str, start: str | None, end: str | None, evergreen: bool = False) -> ParsedDates:
    return ParsedDates(id=pid, event_start=start, event_end=end, evergreen=evergreen)


def test_expired_event_is_updated_and_archived():
    plan = plan_changes([_post("a")], {"a": _parsed("a", "2026-05-10", "2026-05-10")}, TODAY)
    assert plan["updates"] == [
        {"id": "a", "sk": "POST#a", "event_start": "2026-05-10", "event_end": "2026-05-10"}
    ]
    assert len(plan["archives"]) == 1 and plan["archives"][0]["id"] == "a"


def test_future_event_updated_not_archived():
    plan = plan_changes([_post("b")], {"b": _parsed("b", "2026-07-23", "2026-07-25")}, TODAY)
    assert len(plan["updates"]) == 1 and plan["archives"] == []


def test_evergreen_stamped_with_explicit_nulls_never_archived():
    plan = plan_changes([_post("c", tag="guide")], {"c": _parsed("c", None, None, True)}, TODAY)
    assert plan["updates"][0]["event_end"] is None
    assert plan["archives"] == []


def test_event_ending_today_not_archived():
    plan = plan_changes([_post("d")], {"d": _parsed("d", "2026-07-18", "2026-07-20")}, TODAY)
    assert plan["archives"] == []


def test_already_archived_post_gets_dates_but_no_archive_entry():
    plan = plan_changes([_post("e", status="archived")],
                        {"e": _parsed("e", "2026-04-01", "2026-04-30")}, TODAY)
    assert len(plan["updates"]) == 1 and plan["archives"] == []


def test_open_ended_start_only_not_archived():
    plan = plan_changes([_post("f", tag="openNow")], {"f": _parsed("f", "2026-04-18", None)}, TODAY)
    assert plan["archives"] == []


def test_missing_parse_result_warns_and_skips():
    plan = plan_changes([_post("g")], {}, TODAY)
    assert plan["updates"] == [] and plan["archives"] == []
    assert len(plan["warnings"]) == 1


def test_invalid_iso_date_warns_and_skips():
    plan = plan_changes([_post("h")], {"h": _parsed("h", "23. maj 2026", "2026-05-25")}, TODAY)
    assert plan["updates"] == [] and plan["archives"] == []
    assert any("invalid event_start" in w for w in plan["warnings"])


def test_unchanged_dates_skipped_but_archival_still_evaluated():
    posts = [_post("i", event_start="2026-05-10", event_end="2026-05-10")]
    plan = plan_changes(posts, {"i": _parsed("i", "2026-05-10", "2026-05-10")}, TODAY)
    assert plan["updates"] == [] and plan["skipped"] == ["i"]
    assert len(plan["archives"]) == 1


def test_report_dry_run_vs_applied():
    plan = {"updates": [1], "archives": [{"event_end": "2026-05-01", "title": "T", "id": "x", "sk": "s"}],
            "skipped": [], "warnings": ["w"]}
    subject, body = format_report(plan, apply=False, today=TODAY)
    assert "dry-run" in subject and "DRY RUN" in body and "apply=true" in body
    subject, body = format_report(plan, apply=True, today=TODAY)
    assert "applied" in subject and "ARCHIVED" in body


def test_handler_backfill_mode_end_to_end(monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_pipeline_e2e import FakeBedrock, FakeSNS, FakeSession, FakeTable, FakeContext, _existing_post

    monkeypatch.setenv("MODEL_ID", "fake-model")
    monkeypatch.setenv("SNS_TOPIC_ARN", "arn:aws:sns:eu-west-1:1:fake")

    table = FakeTable()
    table.seed(_existing_post("old1", "Forårsfest"))
    table.seed(_existing_post("keep1", "Vandrerute"))

    bedrock = FakeBedrock({"record_parsed_dates": {"items": [
        {"id": "old1", "event_start": "2026-05-01", "event_end": "2026-05-02", "evergreen": False},
        {"id": "keep1", "event_start": None, "event_end": None, "evergreen": True},
    ]}})

    import app
    sns = FakeSNS()
    monkeypatch.setattr(app.boto3, "Session", lambda: FakeSession(table, bedrock, sns))

    # dry run: nothing written
    result = app.lambda_handler({"mode": "backfill", "apply": False}, FakeContext())
    assert result == {"apply": False, "posts": 2, "updates": 2, "archives": 1,
                      "skipped": 0, "warnings": []}
    assert table.items[("POST", "POST#old1")]["status"] == "published"
    assert "dry-run" in sns.published[0][0]

    # apply: dates stamped, expired archived, email says applied
    result = app.lambda_handler({"mode": "backfill", "apply": True}, FakeContext())
    assert result["apply"] is True and result["archives"] == 1
    assert table.items[("POST", "POST#old1")]["status"] == "archived"
    assert table.items[("POST", "POST#keep1")]["event_end"] is None
    assert "applied" in sns.published[-1][0]
