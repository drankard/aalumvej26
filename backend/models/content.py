from __future__ import annotations

from pydantic import BaseModel


class Fact(BaseModel):
    """One row of a page's facts table.

    Every fact must be traceable: either it was extracted from a crawled page
    (`source_url` set) or the site derived it itself (`computed=True`, e.g.
    distance from the house). The pipeline's write-stage gate drops rows that
    satisfy neither — we never publish an unsourced claim about someone else's
    opening hours or prices.
    """

    label: str
    value: str
    source_url: str | None = None
    computed: bool = False


class FaqItem(BaseModel):
    question: str
    answer: str


class PostTranslation(BaseModel):
    title: str
    excerpt: str
    date: str
    # Depth fields. All default-empty so items written before the content
    # expansion still parse; pages render each block only when it's populated.
    tldr: str = ""
    body: str = ""
    facts: list[Fact] = []
    faq: list[FaqItem] = []
    from_house: str = ""


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
    # Written by the pipeline since day one but previously absent here, so the
    # values never reached the frontend and dated posts couldn't emit Event schema.
    event_start: str | None = None
    event_end: str | None = None
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
    event_start: str | None = None
    event_end: str | None = None
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
    event_start: str | None = None
    event_end: str | None = None
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
    # Same depth fields as posts; see PostTranslation.
    body: str = ""
    facts: list[Fact] = []
    faq: list[FaqItem] = []
    from_house: str = ""


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
