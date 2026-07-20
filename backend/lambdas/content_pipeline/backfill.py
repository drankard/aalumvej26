"""Backfill mode: stamp machine-readable event dates on posts, archive expired.

Runs inside the pipeline Lambda (invoked with {"mode": "backfill", "apply": bool})
so the Bedrock call uses the function's own scoped role — the CI deploy role
needs only lambda:InvokeFunction. Dry-run unless apply=true; the plan is
emailed via SNS either way.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from llm import call_structured
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ParsedDates(BaseModel):
    id: str
    event_start: str | None
    event_end: str | None
    evergreen: bool


class ParseResult(BaseModel):
    items: list[ParsedDates]


PARSE_INSTRUCTIONS = """\
Parse the display date of each post below into machine-readable ISO dates.

Rules:
- One-off events, festivals, concerts, exhibitions with a stated period: set
  event_start and event_end (inclusive last day, YYYY-MM-DD), evergreen=false.
  A single-day event has event_start == event_end.
- Season openings / exhibitions with an explicit end date: use the stated end;
  if only an opening date is given, event_start=opening date, event_end=null,
  evergreen=false.
- Recurring/seasonal windows that repeat every year ("Best April - June",
  "Year-round", "spring & autumn", weekly recurring activities without an end),
  guides and routes: evergreen=true, both dates null.
- If ambiguous, prefer the Danish (da) version; the year is 2026 unless stated.
- Return exactly one item per post id, no ids omitted, no ids invented.

Posts (id | tag | da date | en date | title):
"""


def fetch_posts(table) -> list[dict]:
    items, resp = [], table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": "POST"},
    )
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.query(
            KeyConditionExpression="pk = :pk",
            ExpressionAttributeValues={":pk": "POST"},
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))
    return items


def parse_dates(bedrock, model_id: str, posts: list[dict]) -> dict[str, ParsedDates]:
    lines = []
    for p in posts:
        da = p.get("translations", {}).get("da", {})
        en = p.get("translations", {}).get("en", {})
        lines.append(
            f"{p['id']} | {p.get('tag_key', '?')} | {da.get('date', '')} | "
            f"{en.get('date', '')} | {da.get('title', '')}"
        )
    result = call_structured(
        bedrock, model_id, PARSE_INSTRUCTIONS + "\n".join(lines), ParseResult,
        tool_name="record_parsed_dates", max_tokens=16384,
    )
    return {i.id: i for i in result.items}


def plan_changes(posts: list[dict], parsed: dict[str, ParsedDates], today: date) -> dict:
    """Pure decision logic. Archive rule (code, not model):
    published AND event_end parsed AND event_end < today."""
    updates, archives, skipped, warnings = [], [], [], []

    for p in posts:
        pid = p["id"]
        item = parsed.get(pid)
        if item is None:
            warnings.append(f"no parse result for {pid} — untouched")
            continue

        start, end = item.event_start, item.event_end
        bad = False
        for label, value in (("event_start", start), ("event_end", end)):
            if value is not None:
                try:
                    date.fromisoformat(value)
                except ValueError:
                    warnings.append(f"{pid}: invalid {label} {value!r} — untouched")
                    bad = True
                    break
        if bad:
            continue

        already_stamped = "event_start" in p and "event_end" in p
        if already_stamped and p.get("event_start") == start and p.get("event_end") == end:
            skipped.append(pid)
        else:
            updates.append({"id": pid, "sk": p["sk"], "event_start": start, "event_end": end})

        if (
            p.get("status") == "published"
            and end is not None
            and date.fromisoformat(end) < today
        ):
            title = p.get("translations", {}).get("da", {}).get("title", "?")
            archives.append({"id": pid, "sk": p["sk"], "title": title, "event_end": end})

    return {"updates": updates, "archives": archives, "skipped": skipped, "warnings": warnings}


def apply_changes(table, plan: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for u in plan["updates"]:
        table.update_item(
            Key={"pk": "POST", "sk": u["sk"]},
            UpdateExpression="SET event_start = :s, event_end = :e, updated_at = :u",
            ExpressionAttributeValues={
                ":s": u["event_start"], ":e": u["event_end"], ":u": now,
            },
        )
    for a in plan["archives"]:
        table.update_item(
            Key={"pk": "POST", "sk": a["sk"]},
            UpdateExpression="SET #s = :s, updated_at = :u",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "archived", ":u": now},
        )


def format_report(plan: dict, apply: bool, today: date) -> tuple[str, str]:
    mode = "APPLIED" if apply else "DRY RUN — nothing written"
    lines = [
        f"AALUMVEJ26 — Backfill ({mode})",
        f"Date: {today.isoformat()}",
        "",
        f"Date updates: {len(plan['updates'])}",
        f"Archives:     {len(plan['archives'])}",
        f"Unchanged:    {len(plan['skipped'])}",
        f"Warnings:     {len(plan['warnings'])}",
        "",
    ]
    if plan["archives"]:
        lines.append("TO ARCHIVE" if not apply else "ARCHIVED")
        lines += [f"  {a['event_end']}  {a['title']}" for a in plan["archives"]]
        lines.append("")
    if plan["warnings"]:
        lines.append("WARNINGS")
        lines += [f"  {w}" for w in plan["warnings"]]
        lines.append("")
    if not apply:
        lines.append("Re-run the backfill workflow with apply=true to execute this plan.")
    subject = (f"[aalumvej26] backfill {'applied' if apply else 'dry-run'}: "
               f"{len(plan['updates'])} updates, {len(plan['archives'])} archives")
    return subject, "\n".join(lines)


def run_backfill(table, bedrock, model_id: str, today: date, apply: bool) -> dict:
    posts = fetch_posts(table)
    logger.info(f"Backfill: {len(posts)} posts loaded, apply={apply}")
    parsed = parse_dates(bedrock, model_id, posts)
    plan = plan_changes(posts, parsed, today)
    if apply:
        apply_changes(table, plan)
    return {
        "apply": apply,
        "posts": len(posts),
        "updates": len(plan["updates"]),
        "archives": len(plan["archives"]),
        "skipped": len(plan["skipped"]),
        "warnings": plan["warnings"],
        "plan": plan,
    }
