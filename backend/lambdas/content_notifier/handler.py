"""
Content Pipeline Notifier Lambda.

Runs after the content agent finishes. Compares current DynamoDB state
to the pre-run snapshot and sends a diff summary via SNS.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _query_items(table, pk: str) -> list[dict]:
    resp = table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": pk},
    )
    return resp.get("Items", [])


def _published(items: list[dict]) -> list[dict]:
    return [i for i in items if i.get("status") == "published"]


def _archived(items: list[dict]) -> list[dict]:
    return [i for i in items if i.get("status") == "archived"]


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    pipeline = event.get("pipeline", "oplevelser")
    logger.info(f"Content notifier triggered: pipeline={pipeline}")

    table_name = os.environ["TABLE_NAME"]
    topic_arn = os.environ.get("SNS_TOPIC_ARN", "")

    if not topic_arn:
        logger.warning("SNS_TOPIC_ARN not set, skipping")
        return {"statusCode": 200, "body": "skipped"}

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    snapshot_resp = table.get_item(Key={"pk": "PIPELINE_SNAPSHOT", "sk": pipeline})
    snapshot = snapshot_resp.get("Item")
    if not snapshot:
        logger.warning(f"No snapshot found for pipeline={pipeline}")
        return {"statusCode": 200, "body": "no snapshot"}

    old_post_ids = snapshot.get("post_ids", set())
    old_area_ids = snapshot.get("area_ids", set())
    old_post_titles = snapshot.get("post_titles", {})
    old_area_names = snapshot.get("area_names", {})
    if "_empty" in old_post_ids:
        old_post_ids = set()
    if "_empty" in old_area_ids:
        old_area_ids = set()

    posts = _query_items(table, "POST")
    areas = _query_items(table, "AREA")

    published_posts = _published(posts)
    archived_posts = _archived(posts)
    published_areas = _published(areas)

    current_post_ids = {p["id"] for p in published_posts}
    current_area_ids = {a["id"] for a in published_areas}
    archived_post_ids = {p["id"] for p in archived_posts}

    new_post_ids = current_post_ids - old_post_ids
    removed_post_ids = old_post_ids - current_post_ids
    newly_archived = removed_post_ids & archived_post_ids

    new_area_ids = current_area_ids - old_area_ids

    lines = [f"Pipeline: {pipeline}", f"Run snapshot: {snapshot.get('timestamp', 'unknown')}", ""]

    if new_post_ids:
        lines.append(f"NEW POSTS ({len(new_post_ids)}):")
        for p in published_posts:
            if p["id"] in new_post_ids:
                tr = p.get("translations", {}).get("da", {})
                lines.append(f"  + [{p.get('category', '?')}] {tr.get('title', '?')} ({tr.get('date', '')})")
        lines.append("")

    if newly_archived:
        lines.append(f"ARCHIVED POSTS ({len(newly_archived)}):")
        for p in archived_posts:
            if p["id"] in newly_archived:
                tr = p.get("translations", {}).get("da", {})
                title = tr.get("title", old_post_titles.get(p["id"], "?"))
                lines.append(f"  - {title}")
        lines.append("")

    if new_area_ids:
        lines.append(f"NEW AREAS ({len(new_area_ids)}):")
        for a in published_areas:
            if a["id"] in new_area_ids:
                tr = a.get("translations", {}).get("da", {})
                lines.append(f"  + {tr.get('name', '?')} ({tr.get('dist', '')})")
        lines.append("")

    changed_areas = []
    for a in published_areas:
        if a["id"] in old_area_ids and a["id"] not in new_area_ids:
            old_name = old_area_names.get(a["id"], "")
            new_name = a.get("translations", {}).get("da", {}).get("name", "")
            if old_name != new_name:
                changed_areas.append(f"  ~ {old_name} -> {new_name}")
    if changed_areas:
        lines.append("UPDATED AREAS:")
        lines.extend(changed_areas)
        lines.append("")

    if not new_post_ids and not newly_archived and not new_area_ids and not changed_areas:
        lines.append("No changes detected.")

    lines.extend([
        "---",
        f"Total published posts: {len(published_posts)}",
        f"Total archived posts: {len(archived_posts)}",
        f"Total areas: {len(published_areas)}",
    ])

    body = "\n".join(lines)
    n_new = len(new_post_ids)
    n_archived = len(newly_archived)
    n_areas = len(new_area_ids)

    parts = []
    if n_new:
        parts.append(f"{n_new} new")
    if n_archived:
        parts.append(f"{n_archived} archived")
    if n_areas:
        parts.append(f"{n_areas} new areas")
    if not parts:
        parts.append("no changes")

    subject = f"[aalumvej26] {pipeline}: {', '.join(parts)}"

    sns = boto3.client("sns")
    sns.publish(TopicArn=topic_arn, Subject=subject[:100], Message=body)
    logger.info(f"Summary sent: {subject}")

    return {"statusCode": 200, "body": json.dumps({"subject": subject})}
