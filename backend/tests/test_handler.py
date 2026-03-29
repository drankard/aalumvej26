from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("TABLE_NAME", "test-table")


def _make_event(action: str, payload: dict | None = None) -> dict:
    body = {"action": action}
    if payload:
        body["payload"] = payload
    return {"body": json.dumps(body)}


@patch("handler.boto3")
def test_handler_hello(mock_boto3):
    mock_table = MagicMock()
    mock_boto3.resource.return_value.Table.return_value = mock_table

    from handler import lambda_handler

    event = _make_event("hello", {"name": "Test"})
    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["success"] is True
    assert body["data"]["name"] == "Test"
    assert body["data"]["message"] == "Hello, Test!"
    mock_table.put_item.assert_called_once()


@patch("handler.boto3")
def test_handler_list_greetings(mock_boto3):
    mock_table = MagicMock()
    mock_table.query.return_value = {"Items": []}
    mock_boto3.resource.return_value.Table.return_value = mock_table

    from handler import lambda_handler

    event = _make_event("list_greetings")
    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["success"] is True
    assert body["data"] == []


@patch("handler.boto3")
def test_handler_unknown_action(mock_boto3):
    mock_boto3.resource.return_value.Table.return_value = MagicMock()

    from handler import lambda_handler

    event = _make_event("nonexistent")
    result = lambda_handler(event, None)

    body = json.loads(result["body"])
    assert body["success"] is False
    assert "Unknown action" in body["error"]


def test_handler_invalid_json():
    os.environ["TABLE_NAME"] = "test-table"

    from handler import lambda_handler

    result = lambda_handler({"body": "not json"}, None)

    body = json.loads(result["body"])
    assert body["success"] is False
