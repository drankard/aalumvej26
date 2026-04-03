"""
Content Agent Invoker Lambda.

Triggered by EventBridge schedules. Reads current content state from DynamoDB,
builds runtime context variables, and invokes the AgentCore content runtime.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _current_season() -> str:  # duplicated in agentcore_runtimes/content/utils.py
    month = datetime.now().month
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


def _get_published_posts(table) -> list[dict]:
    resp = table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": "POST"},
    )
    return [
        {
            "id": item["id"],
            "title": item.get("translations", {}).get("da", {}).get("title", ""),
            "category": item.get("category", ""),
            "date": item.get("translations", {}).get("da", {}).get("date", ""),
        }
        for item in resp.get("Items", [])
        if item.get("status") == "published"
    ]


def _get_current_areas(table) -> list[dict]:
    resp = table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": "AREA"},
    )
    return [
        {
            "id": item["id"],
            "name": item.get("translations", {}).get("da", {}).get("name", ""),
            "dist": item.get("translations", {}).get("da", {}).get("dist", ""),
            "url": item.get("url", ""),
            "last_updated": item.get("updated_at", ""),
        }
        for item in resp.get("Items", [])
        if item.get("status") == "published"
    ]


def _category_counts(posts: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for p in posts:
        cat = p.get("category", "unknown")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    pipeline = event.get("pipeline", "oplevelser")
    logger.info(f"Content invoker triggered: pipeline={pipeline}")

    table_name = os.environ["TABLE_NAME"]
    runtime_arn = os.environ.get("CONTENT_RUNTIME_ARN", "")

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    posts = _get_published_posts(table)
    areas = _get_current_areas(table)

    context_vars: dict[str, Any] = {
        "current_date": datetime.now(timezone.utc).isoformat()[:10],
        "season": _current_season(),
    }

    if pipeline == "oplevelser":
        context_vars["published_last_30d"] = json.dumps(posts, ensure_ascii=False)
        context_vars["category_counts"] = json.dumps(_category_counts(posts))
    elif pipeline == "omraadet":
        context_vars["current_areas"] = json.dumps(areas, ensure_ascii=False)
        context_vars["oplevelser_last_90d"] = json.dumps(posts, ensure_ascii=False)

    table.put_item(Item={
        "pk": "PIPELINE_SNAPSHOT",
        "sk": pipeline,
        "post_ids": set(p["id"] for p in posts) or {"_empty"},
        "area_ids": set(a["id"] for a in areas) or {"_empty"},
        "post_titles": {p["id"]: p["title"] for p in posts},
        "area_names": {a["id"]: a["name"] for a in areas},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    logger.info(f"Saved pre-run snapshot for pipeline={pipeline}")

    payload = {
        "pipeline": pipeline,
        "context_vars": context_vars,
    }

    if not runtime_arn:
        logger.warning("CONTENT_RUNTIME_ARN not set, skipping invocation")
        return {"statusCode": 200, "body": json.dumps({"skipped": True, "reason": "no runtime ARN"})}

    from botocore.config import Config
    agentcore = boto3.client(
        "bedrock-agentcore",
        config=Config(read_timeout=900, retries={"max_attempts": 0}),
    )
    logger.info(f"Invoking AgentCore runtime: {runtime_arn}")

    response = agentcore.invoke_agent_runtime(
        agentRuntimeArn=runtime_arn,
        payload=json.dumps(payload),
    )

    logger.info(f"AgentCore invocation complete for pipeline={pipeline}")

    sqs = boto3.client("sqs")
    for queue_name, queue_url in [
        ("notifier", os.environ.get("NOTIFIER_QUEUE_URL", "")),
        ("validator", os.environ.get("VALIDATOR_QUEUE_URL", "")),
    ]:
        if queue_url:
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps({"pipeline": pipeline}),
            )
            logger.info(f"{queue_name} queued (SQS delayed): pipeline={pipeline}")

    return {
        "statusCode": 200,
        "body": json.dumps({"pipeline": pipeline, "status": "invoked"}),
    }
