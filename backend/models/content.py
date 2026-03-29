from __future__ import annotations

from pydantic import BaseModel


class PostTranslation(BaseModel):
    title: str
    excerpt: str
    date: str


class Post(BaseModel):
    id: str
    category: str
    tag_key: str
    url: str
    emoji: str
    sort_order: int
    status: str
    relevance_score: int = 0
    source_urls: list[str] = []
    translations: dict[str, PostTranslation]
    created_at: str
    updated_at: str


class PostCreate(BaseModel):
    category: str
    tag_key: str
    url: str
    emoji: str
    sort_order: int = 0
    status: str = "published"
    relevance_score: int = 0
    source_urls: list[str] = []
    translations: dict[str, PostTranslation]


class PostUpdate(BaseModel):
    category: str | None = None
    tag_key: str | None = None
    url: str | None = None
    emoji: str | None = None
    sort_order: int | None = None
    status: str | None = None
    relevance_score: int | None = None
    source_urls: list[str] | None = None
    translations: dict[str, PostTranslation] | None = None


class CategoryTranslation(BaseModel):
    label: str


class Category(BaseModel):
    id: str
    icon: str
    sort_order: int
    translations: dict[str, CategoryTranslation]
    created_at: str
    updated_at: str


class CategoryCreate(BaseModel):
    id: str
    icon: str
    sort_order: int = 0
    translations: dict[str, CategoryTranslation]


class AreaTranslation(BaseModel):
    name: str
    dist: str
    desc: str


class Area(BaseModel):
    id: str
    url: str
    sort_order: int
    status: str
    translations: dict[str, AreaTranslation]
    created_at: str
    updated_at: str


class AreaCreate(BaseModel):
    url: str
    sort_order: int = 0
    status: str = "published"
    translations: dict[str, AreaTranslation]


class AreaUpdate(BaseModel):
    url: str | None = None
    sort_order: int | None = None
    status: str | None = None
    translations: dict[str, AreaTranslation] | None = None
