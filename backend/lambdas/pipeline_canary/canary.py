"""Dead-man canary: alert if a scheduled pipeline run left no PIPELINE_RUN row.

Runs a few hours after each schedule. The pipeline writes its run row even on
failure, so a missing row means the run never happened or died catastrophically
(throttled invoke, misconfiguration, deleted schedule). This is the guarantee
that silence is impossible — the failure mode that went unnoticed for months
in the AgentCore-based system.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def latest_run_age_hours(items: list[dict], now: datetime) -> float | None:
    """Pure: age in hours of the newest run row, None if there are none."""
    if not items:
        return None
    newest = max(i.get("timestamp", "") for i in items)
    try:
        ts = datetime.fromisoformat(newest)
    except ValueError:
        return None
    return (now - ts).total_seconds() / 3600.0


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    pipeline = event.get("pipeline", "oplevelser")
    max_age_hours = float(event.get("max_age_hours", 6))

    table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    resp = table.query(
        KeyConditionExpression=Key("pk").eq("PIPELINE_RUN") & Key("sk").begins_with(f"{pipeline}#"),
        ScanIndexForward=False,
        Limit=5,
    )
    age = latest_run_age_hours(resp.get("Items", []), datetime.now(timezone.utc))

    if age is not None and age <= max_age_hours:
        logger.info(f"Canary OK: {pipeline} ran {age:.1f}h ago (limit {max_age_hours}h)")
        return {"ok": True, "age_hours": age}

    detail = "no run rows found at all" if age is None else f"last run was {age:.1f}h ago"
    message = (
        f"CANARY ALERT — the {pipeline} pipeline did not run as scheduled.\n\n"
        f"Expected a run within the last {max_age_hours:.0f}h, but {detail}.\n"
        f"Check: EventBridge rule enabled? Lambda errors/throttles? "
        f"CloudWatch logs for aalumvej26-content-pipeline."
    )
    logger.error(message)
    topic = os.environ.get("SNS_TOPIC_ARN", "")
    if topic:
        boto3.client("sns").publish(
            TopicArn=topic,
            Subject=f"[aalumvej26] CANARY: {pipeline} pipeline did not run",
            Message=message,
        )
    return {"ok": False, "age_hours": age}
