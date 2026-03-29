from __future__ import annotations

from typing import Any

from actions.registry import register
from models.content import (
    AreaCreate, AreaUpdate, CategoryCreate, PostCreate, PostUpdate,
)
from repositories.content import AreaRepository, CategoryRepository, PostRepository


@register("list_posts")
def list_posts_action(payload: dict[str, Any], *, post_repo: PostRepository, **_: Any) -> list[dict[str, Any]]:
    posts = post_repo.list_published()
    return [p.model_dump() for p in posts]


@register("list_areas")
def list_areas_action(payload: dict[str, Any], *, area_repo: AreaRepository, **_: Any) -> list[dict[str, Any]]:
    areas = area_repo.list_published()
    return [a.model_dump() for a in areas]


@register("list_content")
def list_content_action(payload: dict[str, Any], *, post_repo: PostRepository, area_repo: AreaRepository, category_repo: CategoryRepository, **_: Any) -> dict[str, Any]:
    posts = post_repo.list_published()
    areas = area_repo.list_published()
    categories = category_repo.list_all()
    return {
        "posts": [p.model_dump() for p in posts],
        "areas": [a.model_dump() for a in areas],
        "categories": [c.model_dump() for c in categories],
    }


@register("list_categories")
def list_categories_action(payload: dict[str, Any], *, category_repo: CategoryRepository, **_: Any) -> list[dict[str, Any]]:
    categories = category_repo.list_all()
    return [c.model_dump() for c in categories]


@register("create_category")
def create_category_action(payload: dict[str, Any], *, category_repo: CategoryRepository, **_: Any) -> dict[str, Any]:
    data = CategoryCreate(**payload)
    category = category_repo.create(data)
    return category.model_dump()


@register("list_archived_posts")
def list_archived_posts_action(payload: dict[str, Any], *, post_repo: PostRepository, **_: Any) -> list[dict[str, Any]]:
    posts = post_repo.list_archived()
    return [p.model_dump() for p in posts]


@register("create_post")
def create_post_action(payload: dict[str, Any], *, post_repo: PostRepository, **_: Any) -> dict[str, Any]:
    data = PostCreate(**payload)
    post = post_repo.create(data)
    return post.model_dump()


@register("update_post")
def update_post_action(payload: dict[str, Any], *, post_repo: PostRepository, **_: Any) -> dict[str, Any]:
    post_id = payload.pop("id")
    data = PostUpdate(**payload)
    post = post_repo.update(post_id, data)
    if post is None:
        raise ValueError(f"Post not found: {post_id}")
    return post.model_dump()


@register("delete_post")
def delete_post_action(payload: dict[str, Any], *, post_repo: PostRepository, **_: Any) -> dict[str, Any]:
    post_repo.delete(payload["id"])
    return {"deleted": True}


@register("archive_post")
def archive_post_action(payload: dict[str, Any], *, post_repo: PostRepository, **_: Any) -> dict[str, Any]:
    data = PostUpdate(status="archived")
    post = post_repo.update(payload["id"], data)
    if post is None:
        raise ValueError(f"Post not found: {payload['id']}")
    return post.model_dump()


@register("create_area")
def create_area_action(payload: dict[str, Any], *, area_repo: AreaRepository, **_: Any) -> dict[str, Any]:
    data = AreaCreate(**payload)
    area = area_repo.create(data)
    return area.model_dump()


@register("update_area")
def update_area_action(payload: dict[str, Any], *, area_repo: AreaRepository, **_: Any) -> dict[str, Any]:
    area_id = payload.pop("id")
    data = AreaUpdate(**payload)
    area = area_repo.update(area_id, data)
    if area is None:
        raise ValueError(f"Area not found: {area_id}")
    return area.model_dump()


@register("delete_area")
def delete_area_action(payload: dict[str, Any], *, area_repo: AreaRepository, **_: Any) -> dict[str, Any]:
    area_repo.delete(payload["id"])
    return {"deleted": True}
