"""Source registry: DynamoDB-backed, pipeline-maintained.

Lifecycle:  probation → active → (failing) → retired      closed = manual/known
Pure decision functions are separated from persistence for testability.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from schemas import Source

logger = logging.getLogger(__name__)

RETIRE_AFTER_FAILURES = 4     # consecutive failed *runs* before auto-retire
MAX_AUTO_ADDS_PER_RUN = 2     # curated, not sprawling
REGISTRY_CAP = 55             # non-retired/non-closed sources (41 seeded)

CRAWLABLE_STATUSES = {"probation", "active", "failing"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- pure decision logic ----------

def apply_fetch_outcome(source: Source, ok: bool, now: str | None = None) -> Source:
    """Return an updated copy of the source after one crawl attempt."""
    now = now or _now()
    updates: dict = {"last_checked": now}
    if ok:
        updates["consecutive_failures"] = 0
        updates["last_success"] = now
        if source.status == "failing":
            updates["status"] = "active"
    else:
        failures = source.consecutive_failures + 1
        updates["consecutive_failures"] = failures
        if failures >= RETIRE_AFTER_FAILURES:
            updates["status"] = "retired"
        elif source.status == "active":
            updates["status"] = "failing"
    return source.model_copy(update=updates)


def promote_if_productive(source: Source, productive_domains: set[str]) -> Source:
    """Probation source that yielded a published post graduates to active."""
    if source.status == "probation" and source.domain in productive_domains:
        return source.model_copy(update={"status": "active"})
    return source


def can_add_source(sources: list[Source], added_this_run: int) -> tuple[bool, str]:
    if added_this_run >= MAX_AUTO_ADDS_PER_RUN:
        return False, f"max {MAX_AUTO_ADDS_PER_RUN} auto-adds per run reached"
    live = sum(1 for s in sources if s.status not in ("retired", "closed"))
    if live >= REGISTRY_CAP:
        return False, f"registry cap ({REGISTRY_CAP}) reached — propose a swap instead"
    return True, ""


def known_domains(sources: list[Source]) -> set[str]:
    return {s.domain for s in sources}


def crawlable(sources: list[Source]) -> list[Source]:
    return [s for s in sources if s.status in CRAWLABLE_STATUSES]


def closed_names(sources: list[Source]) -> list[str]:
    return [f"{s.name}: {s.notes}" for s in sources if s.status == "closed"]


# ---------- persistence ----------

def load_sources(table) -> list[Source]:
    items, resp = [], table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": "SOURCE"},
    )
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.query(
            KeyConditionExpression="pk = :pk",
            ExpressionAttributeValues={":pk": "SOURCE"},
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))
    return [Source.model_validate({k: v for k, v in i.items() if k not in ("pk", "sk")})
            for i in items]


def save_source(table, source: Source) -> None:
    item = {"pk": "SOURCE", "sk": source.domain, **source.model_dump()}
    item["tier"] = int(item["tier"])
    item["consecutive_failures"] = int(item["consecutive_failures"])
    table.put_item(Item=item)


def seed_if_empty(table, seeds: list[dict]) -> int:
    """Bootstrap the registry from seeds when no SOURCE items exist. Returns count seeded."""
    existing = load_sources(table)
    if existing:
        return 0
    now = _now()
    count = 0
    for raw in seeds:
        source = Source.model_validate({**raw, "discovered_by": "seed", "added_at": now})
        save_source(table, source)
        count += 1
    logger.info(f"Seeded source registry with {count} sources")
    return count
