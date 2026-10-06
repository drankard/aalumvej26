from __future__ import annotations

import json
import os
from typing import Any

import boto3

import actions.greeting  # noqa: F401 — registers actions
import actions.content  # noqa: F401 — registers actions
from actions.registry import dispatch
from models.base import RpcRequest, RpcResponse
from repositories.base import DynamoDBAdapter
from repositories.greeting import GreetingRepository
from repositories.content import PostRepository, AreaRepository, CategoryRepository

# The public API (POST /rpc, no authentication) is read-only: the site's build needs only these. Content is
# written by the site-publish job straight to the table, with its own write-only role; the write actions stay
# in the code (tests, repositories) but are not reachable from the internet.
PUBLIC_ACTIONS = {"list_content", "list_archived_posts", "list_posts", "list_areas", "list_categories"}


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        body = json.loads(event.get("body", "{}"))
        request = RpcRequest(**body)
        if request.action not in PUBLIC_ACTIONS:
            raise ValueError(f"Unknown action: {request.action} (the public API is read-only)")

        table_name = os.environ["TABLE_NAME"]
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)
        db = DynamoDBAdapter(table)

        greeting_repo = GreetingRepository(db)
        post_repo = PostRepository(db)
        area_repo = AreaRepository(db)
        category_repo = CategoryRepository(db)

        result = dispatch(
            request.action,
            request.payload,
            greeting_repo=greeting_repo,
            post_repo=post_repo,
            area_repo=area_repo,
            category_repo=category_repo,
        )

        response = RpcResponse(success=True, data=result)
    except Exception as e:
        response = RpcResponse(success=False, error=str(e))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": response.model_dump_json(),
    }
