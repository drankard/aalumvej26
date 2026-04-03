"""DynamoDB content tools for reading and writing posts and areas."""
import json
import logging
import os

import boto3
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


@tool
def list_published_posts() -> dict:
    """List all currently published posts from DynamoDB.

    Returns:
        List of published posts with their translations and metadata.
        Use this to check for duplicates before creating new content.
    """
    table = _get_table()
    resp = table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": "POST"},
    )
    posts = [
        item for item in resp.get("Items", [])
        if item.get("status") == "published"
    ]
    return {"posts": posts, "count": len(posts)}


@tool
def list_published_areas() -> dict:
    """List all currently published area cards from DynamoDB.

    Returns:
        List of published area cards with their translations and metadata.
    """
    table = _get_table()
    resp = table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": "AREA"},
    )
    areas = [
        item for item in resp.get("Items", [])
        if item.get("status") == "published"
    ]
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
        translations: Dict of language -> {title, excerpt, date}. Must include 'da'.

    Returns:
        The created post with its generated ID
    """
    import uuid
    from datetime import datetime, timezone

    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "pk": "POST",
        "sk": f"POST#{post_id}",
        "id": post_id,
        "category": category,
        "tag_key": tag_key,
        "url": url,
        "emoji": emoji,
        "sort_order": sort_order,
        "status": "published",
        "relevance_score": 0,
        "source_urls": [url],
        "translations": translations,
        "created_at": now,
        "updated_at": now,
    }

    table = _get_table()
    title = translations.get("da", {}).get("title", "")
    logger.info(f"Writing post to DynamoDB: id={post_id}, category={category}, title={title}")
    try:
        table.put_item(Item=item)
        logger.info(f"Post written successfully: id={post_id}")
    except Exception as e:
        logger.error(f"Failed to write post: id={post_id}, error={e}")
        return {"success": False, "error": str(e)}

    return {"success": True, "post_id": post_id, "title": title}


@tool
def archive_post(post_id: str) -> dict:
    """Archive a post by setting its status to 'archived'.

    Use this for posts whose events have passed or content is no longer current.
    Archived posts are not shown on the main page but remain accessible via the archive.

    Args:
        post_id: ID of the post to archive

    Returns:
        Success status
    """
    from datetime import datetime, timezone

    table = _get_table()
    resp = table.get_item(Key={"pk": "POST", "sk": f"POST#{post_id}"})
    item = resp.get("Item")
    if not item:
        return {"success": False, "error": f"Post {post_id} not found"}

    item["status"] = "archived"
    item["updated_at"] = datetime.now(timezone.utc).isoformat()
    table.put_item(Item=item)

    title = item.get("translations", {}).get("da", {}).get("title", "")
    return {"success": True, "post_id": post_id, "archived_title": title}


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
    from datetime import datetime, timezone

    table = _get_table()
    resp = table.get_item(Key={"pk": "AREA", "sk": f"AREA#{area_id}"})
    item = resp.get("Item")
    if not item:
        return {"success": False, "error": f"Area {area_id} not found"}

    if url:
        item["url"] = url
    if translations:
        existing = item.get("translations", {})
        existing.update(translations)
        item["translations"] = existing
    item["updated_at"] = datetime.now(timezone.utc).isoformat()

    table.put_item(Item=item)
    return {"success": True, "area_id": area_id}


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
        rejections: Breakdown of rejected candidates, e.g. {"duplicate": 3, "low_score": 2, "dead_url": 1, "expired": 1}
        events_next_14d: Count of published events happening in the next 14 days
        notes: Optional free-text notes about the run (unusual findings, recommendations)

    Returns:
        Success status
    """
    from datetime import datetime, timezone

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
    logger.info(f"Writing run summary: pipeline={pipeline}, published={published}, archived={archived}")
    try:
        table.put_item(Item=item)
        logger.info(f"Run summary written: pipeline={pipeline}, timestamp={now}")
    except Exception as e:
        logger.error(f"Failed to write run summary: {e}")
        return {"success": False, "error": str(e)}

    return {"success": True, "timestamp": now}
