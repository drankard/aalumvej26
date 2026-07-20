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


class TranslationEntry(BaseModel):
    title: str
    excerpt: str
    date: str

    @field_validator("title", "excerpt", "date")
    @classmethod
    def _nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v


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
