"""DynamoDB content tools for reading and writing posts and areas."""
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import boto3
from pydantic import BaseModel, field_validator
from strands import tool

logger = logging.getLogger(__name__)

_table = None


def _get_table():
    global _table
    if _table is None:
        table_name = os.environ.get("TABLE_NAME", "aalumvej26-prod")
        region = os.environ.get("AWS_REGION", "eu-west-1")
        _table = boto3.resource("dynamodb", region_name=region).Table(table_name)
    return _table


def _query_all(table, **kwargs) -> list[dict]:
    """Query with automatic pagination."""
    items = []
    resp = table.query(**kwargs)
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.query(ExclusiveStartKey=resp["LastEvaluatedKey"], **kwargs)
        items.extend(resp.get("Items", []))
    return items


VALID_CATEGORIES = {"natur", "kultur", "mad", "surf", "born"}
VALID_TAGS = {
    "event", "guide", "activity", "openNow", "seasonBest",
    "kidFriendly", "natureGem", "localFavorite", "culturalHistory", "bigEvent",
}
REQUIRED_LANGUAGES = {"da", "en", "de"}


class TranslationEntry(BaseModel):
    title: str
    excerpt: str
    date: str


class PostTranslations(BaseModel):
    da: TranslationEntry
    en: TranslationEntry
    de: TranslationEntry


class CreatePostInput(BaseModel):
    category: str
    tag_key: str
    url: str
    emoji: str
    sort_order: int
    translations: PostTranslations

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{v}'. Must be one of: {VALID_CATEGORIES}")
        return v

    @field_validator("tag_key")
    @classmethod
    def validate_tag_key(cls, v: str) -> str:
        if v not in VALID_TAGS:
            raise ValueError(f"Invalid tag_key '{v}'. Must be one of: {VALID_TAGS}")
        return v


@tool
def list_published_posts() -> dict:
    """List all currently published posts from DynamoDB.

    Returns:
        List of published posts with their translations and metadata.
        Use this to check for duplicates before creating new content.
    """
    table = _get_table()
    items = _query_all(
        table,
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": "POST"},
    )
    posts = [item for item in items if item.get("status") == "published"]
    return {"posts": posts, "count": len(posts)}


@tool
def list_published_areas() -> dict:
    """List all currently published area cards from DynamoDB.

    Returns:
        List of published area cards with their translations and metadata.
    """
    table = _get_table()
    items = _query_all(
        table,
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": "AREA"},
    )
    areas = [item for item in items if item.get("status") == "published"]
    return {"areas": areas, "count": len(areas)}


@tool
def create_post(
    category: str,
    tag_key: str,
    url: str,
    emoji: str,
    sort_order: int,
    translations: dict,
) -> dict:
    """Create a new post in DynamoDB.

    Args:
        category: Content category (natur, kultur, mad, surf, born)
        tag_key: Tag identifier (event, guide, activity, etc.)
        url: Source URL for the content
        emoji: Emoji for the card header
        sort_order: Display order (lower = first)
        translations: Dict with keys 'da', 'en', 'de', each containing {title, excerpt, date}.

    Returns:
        The created post with its generated ID, or error if validation fails.
    """
    try:
        validated = CreatePostInput(
            category=category,
            tag_key=tag_key,
            url=url,
            emoji=emoji,
            sort_order=sort_order,
            translations=translations,
        )
    except Exception as e:
        logger.warning(f"Post validation failed: {e}")
        return {"success": False, "error": f"Validation failed: {e}"}

    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "pk": "POST",
        "sk": f"POST#{post_id}",
        "id": post_id,
        "category": validated.category,
        "tag_key": validated.tag_key,
        "url": validated.url,
        "emoji": validated.emoji,
        "sort_order": validated.sort_order,
        "status": "published",
        "relevance_score": 0,
        "source_urls": [validated.url],
        "translations": validated.translations.model_dump(),
        "created_at": now,
        "updated_at": now,
    }

    table = _get_table()
    title = validated.translations.da.title
    logger.info(f"Writing post: id={post_id}, category={validated.category}, title={title}")
    try:
        table.put_item(Item=item)
        logger.info(f"Post written: id={post_id}")
    except Exception as e:
        logger.error(f"Failed to write post: id={post_id}, error={e}")
        return {"success": False, "error": str(e)}

    return {"success": True, "post_id": post_id, "title": title}


@tool
def archive_post(post_id: str) -> dict:
    """Archive a post by setting its status to 'archived'.

    Archived posts are not shown on the main page but remain accessible via the archive.

    Args:
        post_id: ID of the post to archive

    Returns:
        Success status
    """
    table = _get_table()
    now = datetime.now(timezone.utc).isoformat()

    try:
        resp = table.update_item(
            Key={"pk": "POST", "sk": f"POST#{post_id}"},
            UpdateExpression="SET #s = :s, updated_at = :u",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "archived", ":u": now},
            ConditionExpression="attribute_exists(pk)",
            ReturnValues="ALL_NEW",
        )
        title = resp["Attributes"].get("translations", {}).get("da", {}).get("title", "")
        return {"success": True, "post_id": post_id, "archived_title": title}
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return {"success": False, "error": f"Post {post_id} not found"}
    except Exception as e:
        logger.error(f"Failed to archive post {post_id}: {e}")
        return {"success": False, "error": str(e)}


@tool
def update_area(
    area_id: str,
    url: str | None = None,
    translations: dict | None = None,
) -> dict:
    """Update an existing area card in DynamoDB.

    Args:
        area_id: ID of the area to update
        url: New source URL (optional)
        translations: Updated translations dict (optional, merged with existing)

    Returns:
        Success status
    """
    table = _get_table()
    now = datetime.now(timezone.utc).isoformat()

    update_parts = ["updated_at = :u"]
    attr_values: dict[str, Any] = {":u": now}

    if url:
        update_parts.append("url = :url")
        attr_values[":url"] = url

    try:
        if translations:
            resp = table.get_item(Key={"pk": "AREA", "sk": f"AREA#{area_id}"})
            item = resp.get("Item")
            if not item:
                return {"success": False, "error": f"Area {area_id} not found"}
            existing = item.get("translations", {})
            existing.update(translations)
            update_parts.append("translations = :t")
            attr_values[":t"] = existing

        table.update_item(
            Key={"pk": "AREA", "sk": f"AREA#{area_id}"},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeValues=attr_values,
            ConditionExpression="attribute_exists(pk)",
        )
        return {"success": True, "area_id": area_id}
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return {"success": False, "error": f"Area {area_id} not found"}
    except Exception as e:
        logger.error(f"Failed to update area {area_id}: {e}")
        return {"success": False, "error": str(e)}


@tool
def save_run_summary(
    pipeline: str,
    sources_searched: int,
    sources_failed: list[str],
    candidates_found: int,
    published: int,
    archived: int,
    rejections: dict,
    events_next_14d: int,
    notes: str | None = None,
) -> dict:
    """Save a structured run summary to DynamoDB. Call this as your LAST action.

    Args:
        pipeline: Pipeline name ("oplevelser" or "omraadet")
        sources_searched: Number of sources/URLs searched or fetched
        sources_failed: List of source domains that failed (timeout, 404, error)
        candidates_found: Total candidate items evaluated
        published: Number of items published this run
        archived: Number of items archived this run
        rejections: Breakdown of rejected candidates, e.g. {"duplicate": 3, "low_score": 2}
        events_next_14d: Count of published events happening in the next 14 days
        notes: Optional free-text notes about the run

    Returns:
        Success status
    """
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "pk": "PIPELINE_RUN",
        "sk": f"{pipeline}#{now}",
        "pipeline": pipeline,
        "timestamp": now,
        "sources_searched": sources_searched,
        "sources_failed": sources_failed if sources_failed else [],
        "candidates_found": candidates_found,
        "published": published,
        "archived": archived,
        "rejections": rejections if rejections else {},
        "events_next_14d": events_next_14d,
        "notes": notes or "",
    }

    table = _get_table()
    logger.info(f"Writing run summary: pipeline={pipeline}, published={published}")
    try:
        table.put_item(Item=item)
        logger.info(f"Run summary written: pipeline={pipeline}")
    except Exception as e:
        logger.error(f"Failed to write run summary: {e}")
        return {"success": False, "error": str(e)}

    return {"success": True, "timestamp": now}
