from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from models.content import (
    Area, AreaCreate, AreaTranslation, AreaUpdate,
    Category, CategoryCreate, CategoryTranslation,
    Post, PostCreate, PostTranslation, PostUpdate,
)
from repositories.base import DynamoDBAdapter


def _parse_category(item: dict[str, Any]) -> Category:
    translations = {
        lang: CategoryTranslation(**t)
        for lang, t in item.get("translations", {}).items()
    }
    return Category(
        id=item["id"],
        icon=item["icon"],
        sort_order=item.get("sort_order", 0),
        translations=translations,
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )


def _parse_post(item: dict[str, Any]) -> Post:
    translations = {
        lang: PostTranslation(**t)
        for lang, t in item.get("translations", {}).items()
    }
    return Post(
        id=item["id"],
        category=item["category"],
        tag_key=item["tag_key"],
        url=item["url"],
        emoji=item["emoji"],
        sort_order=item.get("sort_order", 0),
        status=item.get("status", "published"),
        relevance_score=item.get("relevance_score", 0),
        source_urls=item.get("source_urls", []),
        translations=translations,
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )


def _parse_area(item: dict[str, Any]) -> Area:
    translations = {
        lang: AreaTranslation(**t)
        for lang, t in item.get("translations", {}).items()
    }
    return Area(
        id=item["id"],
        url=item["url"],
        sort_order=item.get("sort_order", 0),
        status=item.get("status", "published"),
        translations=translations,
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )


class PostRepository:
    def __init__(self, db: DynamoDBAdapter) -> None:
        self._db = db

    def create(self, data: PostCreate) -> Post:
        post_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        translations = {
            lang: t.model_dump() for lang, t in data.translations.items()
        }
        item: dict[str, Any] = {
            "pk": "POST",
            "sk": f"POST#{post_id}",
            "id": post_id,
            "category": data.category,
            "tag_key": data.tag_key,
            "url": data.url,
            "emoji": data.emoji,
            "sort_order": data.sort_order,
            "status": data.status,
            "relevance_score": data.relevance_score,
            "source_urls": data.source_urls,
            "translations": translations,
            "created_at": now,
            "updated_at": now,
        }
        self._db.put_item(item)
        return _parse_post(item)

    def get(self, post_id: str) -> Post | None:
        item = self._db.get_item({"pk": "POST", "sk": f"POST#{post_id}"})
        if item is None:
            return None
        return _parse_post(item)

    def list_published(self) -> list[Post]:
        items = self._db.query("POST")
        posts = [_parse_post(i) for i in items if i.get("status") == "published"]
        posts.sort(key=lambda p: p.sort_order)
        return posts

    def list_all(self) -> list[Post]:
        items = self._db.query("POST")
        posts = [_parse_post(i) for i in items]
        posts.sort(key=lambda p: p.sort_order)
        return posts

    def list_archived(self) -> list[Post]:
        items = self._db.query("POST")
        posts = [_parse_post(i) for i in items if i.get("status") == "archived"]
        posts.sort(key=lambda p: p.sort_order)
        return posts

    def update(self, post_id: str, data: PostUpdate) -> Post | None:
        item = self._db.get_item({"pk": "POST", "sk": f"POST#{post_id}"})
        if item is None:
            return None
        updates = data.model_dump(exclude_none=True)
        if "translations" in updates:
            updates["translations"] = {
                lang: t.model_dump() if hasattr(t, "model_dump") else t
                for lang, t in updates["translations"].items()
            }
        item.update(updates)
        item["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._db.put_item(item)
        return _parse_post(item)

    def delete(self, post_id: str) -> None:
        self._db.delete_item({"pk": "POST", "sk": f"POST#{post_id}"})


class AreaRepository:
    def __init__(self, db: DynamoDBAdapter) -> None:
        self._db = db

    def create(self, data: AreaCreate) -> Area:
        area_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        translations = {
            lang: t.model_dump() for lang, t in data.translations.items()
        }
        item: dict[str, Any] = {
            "pk": "AREA",
            "sk": f"AREA#{area_id}",
            "id": area_id,
            "url": data.url,
            "sort_order": data.sort_order,
            "status": data.status,
            "translations": translations,
            "created_at": now,
            "updated_at": now,
        }
        self._db.put_item(item)
        return _parse_area(item)

    def get(self, area_id: str) -> Area | None:
        item = self._db.get_item({"pk": "AREA", "sk": f"AREA#{area_id}"})
        if item is None:
            return None
        return _parse_area(item)

    def list_published(self) -> list[Area]:
        items = self._db.query("AREA")
        areas = [_parse_area(i) for i in items if i.get("status") == "published"]
        areas.sort(key=lambda a: a.sort_order)
        return areas

    def list_all(self) -> list[Area]:
        items = self._db.query("AREA")
        areas = [_parse_area(i) for i in items]
        areas.sort(key=lambda a: a.sort_order)
        return areas

    def update(self, area_id: str, data: AreaUpdate) -> Area | None:
        item = self._db.get_item({"pk": "AREA", "sk": f"AREA#{area_id}"})
        if item is None:
            return None
        updates = data.model_dump(exclude_none=True)
        if "translations" in updates:
            updates["translations"] = {
                lang: t.model_dump() if hasattr(t, "model_dump") else t
                for lang, t in updates["translations"].items()
            }
        item.update(updates)
        item["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._db.put_item(item)
        return _parse_area(item)

    def delete(self, area_id: str) -> None:
        self._db.delete_item({"pk": "AREA", "sk": f"AREA#{area_id}"})


class CategoryRepository:
    def __init__(self, db: DynamoDBAdapter) -> None:
        self._db = db

    def create(self, data: CategoryCreate) -> Category:
        now = datetime.now(timezone.utc).isoformat()
        translations = {
            lang: t.model_dump() for lang, t in data.translations.items()
        }
        item: dict[str, Any] = {
            "pk": "CATEGORY",
            "sk": f"CATEGORY#{data.id}",
            "id": data.id,
            "icon": data.icon,
            "sort_order": data.sort_order,
            "translations": translations,
            "created_at": now,
            "updated_at": now,
        }
        self._db.put_item(item)
        return _parse_category(item)

    def list_all(self) -> list[Category]:
        items = self._db.query("CATEGORY")
        cats = [_parse_category(i) for i in items]
        cats.sort(key=lambda c: c.sort_order)
        return cats

    def get(self, category_id: str) -> Category | None:
        item = self._db.get_item({"pk": "CATEGORY", "sk": f"CATEGORY#{category_id}"})
        if item is None:
            return None
        return _parse_category(item)
