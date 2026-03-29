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


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        body = json.loads(event.get("body", "{}"))
        request = RpcRequest(**body)

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
