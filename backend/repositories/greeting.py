from __future__ import annotations

import uuid
from datetime import datetime, timezone

from models.greeting import Greeting, GreetingCreate
from repositories.base import DynamoDBAdapter


class GreetingRepository:
    def __init__(self, db: DynamoDBAdapter) -> None:
        self._db = db

    def create(self, data: GreetingCreate) -> Greeting:
        greeting_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "pk": "GREETING",
            "sk": f"GREETING#{greeting_id}",
            "id": greeting_id,
            "name": data.name,
            "message": f"Hello, {data.name}!",
            "created_at": now,
        }
        self._db.put_item(item)
        return Greeting(
            id=greeting_id,
            name=data.name,
            message=f"Hello, {data.name}!",
            created_at=now,
        )

    def list_all(self) -> list[Greeting]:
        items = self._db.query("GREETING", ScanIndexForward=False)
        return [
            Greeting(
                id=item["id"],
                name=item["name"],
                message=item["message"],
                created_at=item["created_at"],
            )
            for item in items
        ]
