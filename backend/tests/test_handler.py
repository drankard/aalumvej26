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
def test_handler_refuses_every_write(mock_boto3):
    """The public API is read-only: no write action reaches the table."""
    mock_table = MagicMock()
    mock_boto3.resource.return_value.Table.return_value = mock_table

    from handler import lambda_handler

    for action in ("hello", "create_post", "update_post", "delete_post", "archive_post",
                   "create_area", "update_area", "delete_area", "create_category"):
        body = json.loads(lambda_handler(_make_event(action, {"id": "x"}), None)["body"])
        assert body["success"] is False, action
        assert "read-only" in body["error"], action
    mock_table.put_item.assert_not_called()
    mock_table.delete_item.assert_not_called()
    mock_table.update_item.assert_not_called()


@patch("handler.boto3")
def test_handler_list_content(mock_boto3):
    mock_table = MagicMock()
    mock_table.query.return_value = {"Items": []}
    mock_boto3.resource.return_value.Table.return_value = mock_table

    from handler import lambda_handler

    body = json.loads(lambda_handler(_make_event("list_content"), None)["body"])
    assert body["success"] is True
    assert body["data"]["posts"] == []


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
