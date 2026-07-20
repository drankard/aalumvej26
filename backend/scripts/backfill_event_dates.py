"""Phase 0 backfill: stamp machine-readable event dates on posts, archive expired ones.

Posts store dates only as localized display strings ("23.-25. maj 2026"), so code
cannot tell whether an event has passed. This one-off script:

1. Loads all POST items from DynamoDB.
2. Asks Claude (one Bedrock call, forced tool use) to parse each post's display
   date into ISO event_start/event_end, or mark it evergreen (recurring seasonal
   windows, "Year-round", guides).
3. Writes event_start/event_end onto every post.
4. Archives published posts whose event_end is in the past (code decision, not model).

Dry-run by default — prints the full plan without writing. Pass --apply to execute.

Usage: triggered via the "Backfill event dates" workflow_dispatch GitHub Action
(only CI has AWS credentials). Run with apply=false first, read the plan in the
job log, then re-run with apply=true.

Direct invocation (from an environment with AWS credentials):
    cd backend
    python -m scripts.backfill_event_dates            # dry run
    python -m scripts.backfill_event_dates --apply    # write
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timezone

import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "aalumvej26-prod")
REGION = os.environ.get("AWS_REGION", "eu-west-1")
MODEL_ID_PARAM = os.environ.get("MODEL_ID_PARAM", "/aalumvej26/ai/model-id")

PARSE_TOOL = {
    "toolSpec": {
        "name": "record_parsed_dates",
        "description": "Record the parsed event dates for every post.",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "event_start": {
                                    "type": ["string", "null"],
                                    "description": "ISO date YYYY-MM-DD, or null if evergreen",
                                },
                                "event_end": {
                                    "type": ["string", "null"],
                                    "description": "ISO date YYYY-MM-DD (inclusive last day), or null if evergreen",
                                },
                                "evergreen": {"type": "boolean"},
                            },
                            "required": ["id", "event_start", "event_end", "evergreen"],
                        },
                    }
                },
                "required": ["items"],
            }
        },
    }
}

PARSE_INSTRUCTIONS = """\
Parse the display date of each post below into machine-readable ISO dates.

Rules:
- One-off events, festivals, concerts, exhibitions with a stated period: set
  event_start and event_end (inclusive last day, YYYY-MM-DD), evergreen=false.
  A single-day event has event_start == event_end.
- "Open from <month>" season openings, exhibitions with an explicit end date:
  use the stated end; if only an opening date is given, event_start=opening date,
  event_end=null, evergreen=false.
- Recurring/seasonal windows that repeat every year ("Best April - June",
  "Year-round", "spring & autumn", weekly recurring activities without an end),
  guides and routes: evergreen=true, both dates null.
- If a date string is ambiguous, prefer the Danish (da) version; the year is 2026
  unless stated otherwise.
- Return exactly one item per post id, no ids omitted, no ids invented.

Posts (id | tag | da date | en date | title):
"""


def get_model_id(session: boto3.Session) -> str:
    if os.environ.get("MODEL_ID"):
        return os.environ["MODEL_ID"]
    ssm = session.client("ssm", region_name=REGION)
    return ssm.get_parameter(Name=MODEL_ID_PARAM)["Parameter"]["Value"]


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


def parse_dates_via_bedrock(session: boto3.Session, model_id: str, posts: list[dict]) -> dict[str, dict]:
    """One Converse call, forced tool use. Returns {post_id: parsed_item}."""
    lines = []
    for p in posts:
        da = p.get("translations", {}).get("da", {})
        en = p.get("translations", {}).get("en", {})
        lines.append(
            f"{p['id']} | {p.get('tag_key', '?')} | {da.get('date', '')} | "
            f"{en.get('date', '')} | {da.get('title', '')}"
        )
    prompt = PARSE_INSTRUCTIONS + "\n".join(lines)

    client = session.client("bedrock-runtime", region_name=REGION)
    resp = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        toolConfig={
            "tools": [PARSE_TOOL],
            "toolChoice": {"tool": {"name": "record_parsed_dates"}},
        },
        inferenceConfig={"maxTokens": 16384},
    )
    for block in resp["output"]["message"]["content"]:
        if "toolUse" in block:
            items = block["toolUse"]["input"]["items"]
            return {i["id"]: i for i in items}
    raise RuntimeError("Model returned no tool call")


def plan_changes(posts: list[dict], parsed: dict[str, dict], today: date) -> dict:
    """Pure decision logic: what to update, what to archive, what to flag.

    Archive rule (code, not model): published AND event_end parsed AND event_end < today.
    """
    updates, archives, skipped, warnings = [], [], [], []

    for p in posts:
        pid = p["id"]
        item = parsed.get(pid)
        if item is None:
            warnings.append(f"no parse result for {pid} — untouched")
            continue

        start, end = item.get("event_start"), item.get("event_end")
        for label, value in (("event_start", start), ("event_end", end)):
            if value is not None:
                try:
                    date.fromisoformat(value)
                except ValueError:
                    warnings.append(f"{pid}: invalid {label} {value!r} — untouched")
                    item = None
                    break
        if item is None:
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
    archive_ids = {a["id"] for a in plan["archives"]}

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

    print(f"\nApplied: {len(plan['updates'])} date updates, {len(archive_ids)} archived.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args()

    session = boto3.Session()
    table = session.resource("dynamodb", region_name=REGION).Table(TABLE_NAME)
    model_id = get_model_id(session)

    posts = fetch_posts(table)
    print(f"Loaded {len(posts)} posts from {TABLE_NAME}; parsing dates with {model_id} ...")

    parsed = parse_dates_via_bedrock(session, model_id, posts)
    plan = plan_changes(posts, parsed, today=datetime.now(timezone.utc).date())

    print(f"\nPlan: {len(plan['updates'])} date updates, {len(plan['archives'])} archives, "
          f"{len(plan['skipped'])} already current, {len(plan['warnings'])} warnings")
    for a in plan["archives"]:
        print(f"  ARCHIVE  {a['event_end']}  {a['title']}")
    for w in plan["warnings"]:
        print(f"  WARN     {w}")

    if not args.apply:
        print("\nDry run — nothing written. Re-run with --apply to execute.")
        return 0

    apply_changes(table, plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
