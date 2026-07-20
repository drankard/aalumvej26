"""Tests for the Phase 0 backfill decision logic (plan_changes is pure)."""
from __future__ import annotations

from datetime import date

from scripts.backfill_event_dates import plan_changes

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


def _parsed(pid: str, start: str | None, end: str | None, evergreen: bool = False) -> dict:
    return {"id": pid, "event_start": start, "event_end": end, "evergreen": evergreen}


def test_expired_event_is_updated_and_archived():
    posts = [_post("a")]
    parsed = {"a": _parsed("a", "2026-05-10", "2026-05-10")}
    plan = plan_changes(posts, parsed, TODAY)
    assert plan["updates"] == [
        {"id": "a", "sk": "POST#a", "event_start": "2026-05-10", "event_end": "2026-05-10"}
    ]
    assert len(plan["archives"]) == 1
    assert plan["archives"][0]["id"] == "a"


def test_future_event_updated_not_archived():
    posts = [_post("b")]
    parsed = {"b": _parsed("b", "2026-07-23", "2026-07-25")}
    plan = plan_changes(posts, parsed, TODAY)
    assert len(plan["updates"]) == 1
    assert plan["archives"] == []


def test_evergreen_never_archived():
    posts = [_post("c", tag="guide")]
    parsed = {"c": _parsed("c", None, None, evergreen=True)}
    plan = plan_changes(posts, parsed, TODAY)
    assert plan["updates"][0]["event_end"] is None
    assert plan["archives"] == []


def test_event_ending_today_not_archived():
    posts = [_post("d")]
    parsed = {"d": _parsed("d", "2026-07-18", "2026-07-20")}
    plan = plan_changes(posts, parsed, TODAY)
    assert plan["archives"] == []


def test_already_archived_post_gets_dates_but_no_archive_entry():
    posts = [_post("e", status="archived")]
    parsed = {"e": _parsed("e", "2026-04-01", "2026-04-30")}
    plan = plan_changes(posts, parsed, TODAY)
    assert len(plan["updates"]) == 1
    assert plan["archives"] == []


def test_open_ended_start_only_not_archived():
    # "Opens 18 April 2026" — start but no end: cannot expire.
    posts = [_post("f", tag="openNow")]
    parsed = {"f": _parsed("f", "2026-04-18", None)}
    plan = plan_changes(posts, parsed, TODAY)
    assert plan["archives"] == []


def test_missing_parse_result_warns_and_skips():
    posts = [_post("g")]
    plan = plan_changes(posts, {}, TODAY)
    assert plan["updates"] == []
    assert plan["archives"] == []
    assert len(plan["warnings"]) == 1


def test_invalid_iso_date_warns_and_skips():
    posts = [_post("h")]
    parsed = {"h": _parsed("h", "23. maj 2026", "2026-05-25")}
    plan = plan_changes(posts, parsed, TODAY)
    assert plan["updates"] == []
    assert plan["archives"] == []
    assert any("invalid event_start" in w for w in plan["warnings"])


def test_unchanged_dates_are_skipped_but_archival_still_evaluated():
    posts = [_post("i", event_start="2026-05-10", event_end="2026-05-10")]
    parsed = {"i": _parsed("i", "2026-05-10", "2026-05-10")}
    plan = plan_changes(posts, parsed, TODAY)
    assert plan["updates"] == []
    assert plan["skipped"] == ["i"]
    assert len(plan["archives"]) == 1
