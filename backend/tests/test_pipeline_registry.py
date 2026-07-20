"""Tests for source-registry lifecycle decisions (pure functions)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas" / "content_pipeline"))

from registry import (  # noqa: E402
    MAX_AUTO_ADDS_PER_RUN,
    REGISTRY_CAP,
    RETIRE_AFTER_FAILURES,
    apply_fetch_outcome,
    can_add_source,
    crawlable,
    promote_if_productive,
)
from schemas import Source  # noqa: E402

NOW = "2026-07-20T00:00:00+00:00"


def _src(**kw) -> Source:
    base = dict(domain="example.dk", name="Example", url="https://example.dk", tier=2)
    return Source.model_validate({**base, **kw})


def test_success_resets_failures_and_recovers_failing():
    s = _src(status="failing", consecutive_failures=3)
    out = apply_fetch_outcome(s, ok=True, now=NOW)
    assert out.status == "active"
    assert out.consecutive_failures == 0
    assert out.last_success == NOW


def test_failure_marks_active_source_failing():
    out = apply_fetch_outcome(_src(status="active"), ok=False, now=NOW)
    assert out.status == "failing"
    assert out.consecutive_failures == 1
    assert out.last_success is None


def test_retire_after_threshold():
    s = _src(status="failing", consecutive_failures=RETIRE_AFTER_FAILURES - 1)
    out = apply_fetch_outcome(s, ok=False, now=NOW)
    assert out.status == "retired"


def test_probation_failure_can_retire_without_active_detour():
    s = _src(status="probation", consecutive_failures=RETIRE_AFTER_FAILURES - 1)
    out = apply_fetch_outcome(s, ok=False, now=NOW)
    assert out.status == "retired"


def test_probation_promoted_only_when_productive():
    s = _src(status="probation")
    assert promote_if_productive(s, {"example.dk"}).status == "active"
    assert promote_if_productive(s, {"other.dk"}).status == "probation"
    # active sources unaffected
    a = _src(status="active")
    assert promote_if_productive(a, {"example.dk"}).status == "active"


def test_add_source_respects_per_run_cap():
    ok, _ = can_add_source([], added_this_run=MAX_AUTO_ADDS_PER_RUN - 1)
    assert ok
    ok, reason = can_add_source([], added_this_run=MAX_AUTO_ADDS_PER_RUN)
    assert not ok and "auto-adds" in reason


def test_add_source_respects_registry_cap():
    live = [_src(domain=f"d{i}.dk") for i in range(REGISTRY_CAP)]
    ok, reason = can_add_source(live, added_this_run=0)
    assert not ok and "cap" in reason
    # retired/closed don't count toward the cap
    mixed = live[:-1] + [_src(domain="dead.dk", status="retired")]
    ok, _ = can_add_source(mixed, added_this_run=0)
    assert ok


def test_crawlable_excludes_retired_and_closed():
    sources = [
        _src(domain="a.dk", status="active"),
        _src(domain="p.dk", status="probation"),
        _src(domain="f.dk", status="failing"),
        _src(domain="r.dk", status="retired"),
        _src(domain="c.dk", status="closed"),
    ]
    assert {s.domain for s in crawlable(sources)} == {"a.dk", "p.dk", "f.dk"}


def test_seed_data_is_valid():
    from seeds import SEED_SOURCES
    parsed = [Source.model_validate(s) for s in SEED_SOURCES]
    assert len(parsed) == 44
    assert sum(1 for s in parsed if s.status == "closed") == 3
    assert all(1 <= s.tier <= 4 for s in parsed)
    domains = [s.domain for s in parsed]
    assert len(domains) == len(set(domains)), "duplicate domains in seeds"
