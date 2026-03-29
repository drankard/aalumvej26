from __future__ import annotations

from typing import Any


class DynamoDBAdapter:
    def __init__(self, table: Any) -> None:
        self._table = table

    def put_item(self, item: dict[str, Any]) -> None:
        self._table.put_item(Item=item)

    def get_item(self, key: dict[str, str]) -> dict[str, Any] | None:
        response = self._table.get_item(Key=key)
        return response.get("Item")

    def query(self, pk: str, **kwargs: Any) -> list[dict[str, Any]]:
        response = self._table.query(
            KeyConditionExpression="pk = :pk",
            ExpressionAttributeValues={":pk": pk},
            **kwargs,
        )
        return response.get("Items", [])
