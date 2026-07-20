"""Tests for pipeline stage logic — pure functions + mocked-edge flows."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas" / "content_pipeline"))

from schemas import CandidateEvent, Judgment, PostTranslations, TranslationEntry, WriteResult, PostCopy  # noqa: E402
from stages import (  # noqa: E402
    MAX_PUBLISH_PER_RUN,
    RunState,
    accepted_candidates,
    events_next_14d,
    filter_candidates,
    plan_expired,
    stage_write_publish,
)

TODAY = date(2026, 7, 20)


def _state(**kw) -> RunState:
    defaults = dict(pipeline="oplevelser", today=TODAY, season="summer", model_id="m")
    return RunState(**{**defaults, **kw})


def _cand(title: str, start: str | None = None, end: str | None = None, **kw) -> CandidateEvent:
    base = dict(title=title, event_start=start, event_end=end,
                source_url=f"https://src.dk/{title[:8]}", category="kultur")
    return CandidateEvent.model_validate({**base, **kw})


def _post(title: str, url: str = "", status: str = "published", **extra) -> dict:
    return {"status": status, "url": url,
            "translations": {"da": {"title": title, "date": "x"}}, **extra}


# ---------- plan_expired ----------

def test_plan_expired_only_past_end_published():
    posts = [
        _post("gone", event_end="2026-07-19", sk="POST#1"),
        _post("today", event_end="2026-07-20", sk="POST#2"),
        _post("evergreen", event_end=None, sk="POST#3"),
        _post("already-archived", status="archived", event_end="2026-01-01", sk="POST#4"),
        _post("unstamped", sk="POST#5"),
    ]
    assert [p["sk"] for p in plan_expired(posts, TODAY)] == ["POST#1"]


# ---------- filter_candidates ----------

def test_filter_rejects_expired_and_far_future():
    kept, rej = filter_candidates(
        [_cand("past", "2026-07-01", "2026-07-10"),
         _cand("far", "2026-12-01", "2026-12-02"),
         _cand("ok", "2026-08-01", "2026-08-02")],
        published=[], today=TODAY)
    assert [c.title for c in kept] == ["ok"]
    assert rej == {"expired": 1, "too_far_future": 1}


def test_filter_rejects_duplicates_by_title_and_url():
    published = [_post("Krabbefest i Agger 2026", url="https://a.dk/x")]
    kept, rej = filter_candidates(
        [_cand("Krabbefest i Agger"),                       # fuzzy title match
         _cand("Unik ny ting", source_url="https://a.dk/x"),  # url match
         _cand("Helt andet arrangement")],
        published=published, today=TODAY)
    assert [c.title for c in kept] == ["Helt andet arrangement"]
    assert rej["duplicate"] == 2


def test_filter_dedups_within_batch():
    kept, rej = filter_candidates(
        [_cand("Thy Rock festival 2026"), _cand("Thy Rock Festival 2026 ")],
        published=[], today=TODAY)
    assert len(kept) == 1
    assert rej["duplicate"] == 1


def test_evergreen_passes_without_dates():
    kept, rej = filter_candidates([_cand("Vandrerute", evergreen=True)], [], TODAY)
    assert len(kept) == 1 and not rej


# ---------- accepted_candidates ----------

def test_accepted_sorted_by_score_and_capped():
    state = _state()
    state.candidates = [_cand(f"cand {i}") for i in range(12)]
    state.judgments = [Judgment(title=f"cand {i}", accept=True, score=(i % 10) + 1, reason="r")
                       for i in range(12)]
    pairs = accepted_candidates(state)
    assert len(pairs) == MAX_PUBLISH_PER_RUN
    scores = [j.score for _, j in pairs]
    assert scores == sorted(scores, reverse=True)


def test_accepted_ignores_rejected_and_unmatched():
    state = _state()
    state.candidates = [_cand("known")]
    state.judgments = [
        Judgment(title="known", accept=False, score=2, reason="r", rejection_key="not_relevant"),
        Judgment(title="ghost", accept=True, score=9, reason="r"),
    ]
    assert accepted_candidates(state) == []


# ---------- stage_write_publish ----------

def _copy(title: str, url: str = "https://ok.dk/e") -> PostCopy:
    tr = TranslationEntry(title=title, excerpt="God oplevelse i Thy.", date="1. august 2026")
    return PostCopy(title_ref=title, category="kultur", tag_key="event", url=url, emoji="🎵",
                    event_start="2026-08-01", event_end="2026-08-01",
                    translations=PostTranslations(da=tr, en=tr, de=tr))


def test_write_publish_puts_items_and_blocks_dead_urls(monkeypatch):
    state = _state()
    state.candidates = [_cand("Koncert A"), _cand("Koncert B")]
    state.judgments = [Judgment(title="Koncert A", accept=True, score=9, reason="r"),
                       Judgment(title="Koncert B", accept=True, score=7, reason="r")]
    table = MagicMock()

    import stages as st
    monkeypatch.setattr(st, "call_structured", lambda *a, **k: WriteResult(
        posts=[_copy("Koncert A"), _copy("Koncert B", url="https://dead.dk/x")]))

    stage_write_publish(state, table, bedrock=MagicMock(),
                        url_checker=lambda u: "dead" not in u)

    assert len(state.published) == 1
    assert state.published[0]["title"] == "Koncert A"
    assert state.rejections.get("dead_url") == 1
    item = table.put_item.call_args.kwargs["Item"]
    assert item["status"] == "published"
    assert item["event_start"] == "2026-08-01"
    assert item["run_id"] == state.run_id
    assert set(item["translations"].keys()) == {"da", "en", "de"}


def test_write_publish_no_accepted_is_noop():
    state = _state()
    table = MagicMock()
    stage_write_publish(state, table, bedrock=MagicMock(), url_checker=lambda u: True)
    table.put_item.assert_not_called()


# ---------- events_next_14d ----------

def test_events_next_14d_counts_upcoming_and_ongoing():
    posts = [
        _post("upcoming", event_start="2026-07-25", event_end="2026-07-26"),
        _post("ongoing", event_start="2026-07-10", event_end="2026-07-30"),
        _post("too-far", event_start="2026-09-01", event_end="2026-09-02"),
        _post("past", event_start="2026-07-01", event_end="2026-07-02"),
        _post("evergreen"),
        _post("archived-upcoming", status="archived", event_start="2026-07-22", event_end="2026-07-22"),
    ]
    assert events_next_14d(posts, TODAY) == 2
