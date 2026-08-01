"""Pydantic schemas for the content pipeline. All layer boundaries are typed."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES = {"natur", "kultur", "mad", "surf", "born"}
VALID_TAGS = {
    "event", "guide", "activity", "openNow", "seasonBest",
    "kidFriendly", "natureGem", "localFavorite", "culturalHistory", "bigEvent",
}

SourceStatus = Literal["probation", "active", "failing", "retired", "closed"]


class Source(BaseModel):
    domain: str
    name: str
    url: str
    tier: int = Field(ge=1, le=4)
    type: str = ""
    notes: str = ""
    status: SourceStatus = "active"
    consecutive_failures: int = 0
    last_success: str | None = None
    last_checked: str | None = None
    discovered_by: str = "seed"
    added_at: str | None = None


class CrawlResult(BaseModel):
    domain: str
    url: str
    ok: bool
    status: int | None = None
    text: str = ""
    error: str | None = None


class CandidateEvent(BaseModel):
    """One extracted candidate from crawled text. Dates are ISO or null (evergreen)."""
    title: str
    event_start: str | None = None
    event_end: str | None = None
    evergreen: bool = False
    location: str = ""
    source_url: str
    source_domain: str = ""
    category: str
    details: str = ""

    @field_validator("category")
    @classmethod
    def _cat(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"invalid category {v!r}, must be one of {sorted(VALID_CATEGORIES)}")
        return v


class ExtractResult(BaseModel):
    candidates: list[CandidateEvent]


class Judgment(BaseModel):
    title: str
    accept: bool
    score: int = Field(ge=1, le=10)
    reason: str
    rejection_key: str | None = None  # duplicate|out_of_range|expired|too_far_future|insufficient_detail|not_relevant


class JudgeResult(BaseModel):
    judgments: list[Judgment]


class SourceVerdict(BaseModel):
    domain: str
    relevant: bool
    confidence: Literal["high", "medium", "low"]
    tier: int = Field(ge=1, le=4)
    type: str = ""
    suggested_name: str = ""
    reasoning: str
    reject_reason: str | None = None


class SourceJudgeResult(BaseModel):
    verdicts: list[SourceVerdict]


MAX_FACTS = 10
MAX_FAQ = 5


class Fact(BaseModel):
    """One row of the facts table, with provenance.

    A fact is publishable only if it came from a crawled source (`source_url`)
    or the site derived it itself (`computed=True`). Anything else is the model
    guessing at a third party's opening hours or prices, which we never publish.
    """

    label: str
    value: str
    source_url: str | None = None
    computed: bool = False


class FaqItem(BaseModel):
    question: str
    answer: str


def drop_unsourced_facts(rows: object) -> tuple[list, int]:
    """Split fact rows into (publishable, dropped_count).

    Kept when computed=True or source_url is an absolute http(s) URL. Dropping
    rather than raising is deliberate: one hallucinated price should cost that
    row, not the whole post.
    """
    if not isinstance(rows, list):
        return [], 0
    kept: list = []
    for row in rows:
        d = row if isinstance(row, dict) else row.__dict__
        label = str(d.get("label") or "").strip()
        value = str(d.get("value") or "").strip()
        if not label or not value:
            continue
        if d.get("computed"):
            kept.append(row)
            continue
        url = str(d.get("source_url") or "").strip()
        if url.startswith("http://") or url.startswith("https://"):
            kept.append(row)
    return kept[:MAX_FACTS], len(rows) - len(kept[:MAX_FACTS])


class DepthFields(BaseModel):
    """The depth block, with the provenance gate applied.

    Shared by the write stage (new posts) and the depth backfill (existing
    posts) so both go through exactly one implementation of the fact rules —
    a second copy would drift, and the copy that drifted would be the one
    publishing invented opening hours.
    """

    tldr: str = ""
    body: str = ""
    facts: list[Fact] = []
    faq: list[FaqItem] = []

    @field_validator("facts", mode="before")
    @classmethod
    def _only_sourced_facts(cls, v: object) -> list:
        kept, _ = drop_unsourced_facts(v)
        return kept

    @field_validator("faq", mode="before")
    @classmethod
    def _cap_faq(cls, v: object) -> object:
        return v[:MAX_FAQ] if isinstance(v, list) else v


class TranslationEntry(DepthFields):
    title: str
    excerpt: str
    date: str

    @field_validator("title", "excerpt", "date")
    @classmethod
    def _nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v


class DepthTranslations(BaseModel):
    da: DepthFields
    en: DepthFields
    de: DepthFields


class PostDepth(BaseModel):
    """Depth generated for one already-published post."""

    title_ref: str
    translations: DepthTranslations


class DepthResult(BaseModel):
    posts: list[PostDepth]


class PostTranslations(BaseModel):
    da: TranslationEntry
    en: TranslationEntry
    de: TranslationEntry


class PostCopy(BaseModel):
    """Write-stage output for one post; the pre-publish validation gate."""
    title_ref: str  # candidate title this copy belongs to
    category: str
    tag_key: str
    url: str
    emoji: str
    event_start: str | None = None
    event_end: str | None = None
    translations: PostTranslations

    @field_validator("category")
    @classmethod
    def _cat(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"invalid category {v!r}")
        return v

    @field_validator("tag_key")
    @classmethod
    def _tag(cls, v: str) -> str:
        if v not in VALID_TAGS:
            raise ValueError(f"invalid tag_key {v!r}")
        return v

    @field_validator("emoji")
    @classmethod
    def _emoji(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("emoji required")
        return v


class WriteResult(BaseModel):
    posts: list[PostCopy]


class AreaAudit(BaseModel):
    area_id: str
    verdict: Literal["unchanged", "minor_update", "major_update", "broken_link"]
    reasoning: str
    url: str | None = None
    translations: dict | None = None  # {da|en|de: {name, dist, desc}} when updating


class AreaAuditResult(BaseModel):
    audits: list[AreaAudit]
    new_card_recommendations: list[str] = []
