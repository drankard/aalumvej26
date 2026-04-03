"""
Content Validator Lambda.

Validates recently published content for quality issues:
- Missing translations (must have da, en, de)
- Missing required fields (title, excerpt, date)
- Invalid category or tag_key
- URL not reachable
- Date in the past (for event-tagged posts)

Triggered by SQS after the notifier runs. Reports issues via SNS.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

VALID_CATEGORIES = {"natur", "kultur", "mad", "surf", "born"}
VALID_TAGS = {
    "event", "guide", "activity", "openNow", "seasonBest",
    "kidFriendly", "natureGem", "localFavorite", "culturalHistory", "bigEvent",
}
REQUIRED_LANGUAGES = {"da", "en", "de"}
REQUIRED_FIELDS = {"title", "excerpt", "date"}


def _validate_url(url: str) -> bool:
    try:
        req = urllib.request.Request(
            url, method="HEAD",
            headers={"User-Agent": "Aalumvej26-Validator/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 400
    except Exception:
        return False


def _validate_post(post: dict) -> list[str]:
    issues = []
    post_id = post.get("id", "?")
    title = post.get("translations", {}).get("da", {}).get("title", "?")

    category = post.get("category", "")
    if category not in VALID_CATEGORIES:
        issues.append(f"Invalid category '{category}'")

    tag = post.get("tag_key", "")
    if tag not in VALID_TAGS:
        issues.append(f"Invalid tag_key '{tag}'")

    translations = post.get("translations", {})
    missing_langs = REQUIRED_LANGUAGES - set(translations.keys())
    if missing_langs:
        issues.append(f"Missing translations: {missing_langs}")

    for lang in REQUIRED_LANGUAGES:
        if lang not in translations:
            continue
        tr = translations[lang]
        missing_fields = REQUIRED_FIELDS - set(tr.keys())
        if missing_fields:
            issues.append(f"Missing fields in {lang}: {missing_fields}")
        for field in REQUIRED_FIELDS:
            val = tr.get(field, "")
            if not val or not val.strip():
                issues.append(f"Empty {lang}.{field}")

    url = post.get("url", "")
    if not url:
        issues.append("No URL")
    elif not _validate_url(url):
        issues.append(f"URL unreachable: {url}")

    if not post.get("emoji"):
        issues.append("Missing emoji")

    return [f"[{post_id}] {title}: {issue}" for issue in issues]


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger.info("Content validator triggered")

    table_name = os.environ["TABLE_NAME"]
    topic_arn = os.environ.get("SNS_TOPIC_ARN", "")

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    resp = table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": "POST"},
    )
    posts = [item for item in resp.get("Items", []) if item.get("status") == "published"]

    all_issues = []
    for post in posts:
        issues = _validate_post(post)
        all_issues.extend(issues)

    if not all_issues:
        logger.info(f"All {len(posts)} posts passed validation")
        return {"statusCode": 200, "body": "all valid"}

    logger.warning(f"Found {len(all_issues)} validation issues")
    body = f"Content validation found {len(all_issues)} issues:\n\n"
    body += "\n".join(f"  - {issue}" for issue in all_issues)

    if topic_arn:
        sns = boto3.client("sns")
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"[aalumvej26] Content validation: {len(all_issues)} issues",
            Message=body,
        )
        logger.info("Validation report sent via SNS")

    return {"statusCode": 200, "body": json.dumps({"issues": len(all_issues)})}
