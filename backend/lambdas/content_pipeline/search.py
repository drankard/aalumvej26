"""Search providers for source/event discovery. Danish locale is non-negotiable.

Provider selection via SEARCH_PROVIDER env (serpapi|none). Missing key or
provider errors degrade to an explicit skip that lands in the run report —
search failure must never kill a run (registry crawl carries the pipeline).
"""
from __future__ import annotations

import logging
import os

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

SEASONAL_QUERIES = {
    "spring": ["det sker thy forår 2026", "påske aktiviteter thy", "nyt åbner thy 2026"],
    "summer": ["det sker thy sommer 2026", "sommerferie aktiviteter thy mors", "festival thy 2026"],
    "autumn": ["det sker thy efterår 2026", "østers limfjorden arrangement", "efterårsferie thy aktiviteter"],
    "winter": ["julemarked thy 2026", "det sker thy vinter", "vinteraktiviteter nationalpark thy"],
}
DISCOVERY_QUERIES = ["ny restaurant thy 2026", "ny attraktion thy mors 2026", "nyt i agger"]


class SearchHit(BaseModel):
    title: str
    url: str
    snippet: str = ""


class NullProvider:
    """No search configured — stage skips, run report says so."""
    name = "none"

    def search(self, query: str, max_results: int = 8) -> list[SearchHit]:
        return []


class SerpApiProvider:
    """Google.dk results via SerpAPI (free plan: 250/mo)."""
    name = "serpapi"

    def __init__(self, api_key: str):
        self._key = api_key

    def search(self, query: str, max_results: int = 8) -> list[SearchHit]:
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.get("https://serpapi.com/search.json", params={
                    "q": query,
                    "google_domain": "google.dk",
                    "gl": "dk",
                    "hl": "da",
                    "num": max_results,
                    "api_key": self._key,
                })
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.warning(f"SerpAPI search failed for {query!r}: {e}")
            return []
        hits = []
        for r in data.get("organic_results", [])[:max_results]:
            if r.get("link"):
                hits.append(SearchHit(title=r.get("title", ""), url=r["link"],
                                      snippet=r.get("snippet", "")))
        return hits


def get_provider(ssm_client=None) -> NullProvider | SerpApiProvider:
    provider = os.environ.get("SEARCH_PROVIDER", "serpapi").lower()
    if provider in ("", "none"):
        return NullProvider()
    if provider == "serpapi":
        param = os.environ.get("SERPAPI_KEY_PARAM", "/aalumvej26/search/serpapi-key")
        try:
            import boto3
            ssm = ssm_client or boto3.client("ssm")
            key = ssm.get_parameter(Name=param, WithDecryption=True)["Parameter"]["Value"]
            return SerpApiProvider(key)
        except Exception as e:
            logger.warning(f"SerpAPI key unavailable ({param}): {e} — search disabled this run")
            return NullProvider()
    logger.warning(f"Unknown SEARCH_PROVIDER {provider!r} — search disabled")
    return NullProvider()


def build_queries(season: str, gap_categories: list[str]) -> list[str]:
    """Seasonal + discovery + gap-driven queries. Bounded and deterministic."""
    queries = list(SEASONAL_QUERIES.get(season, SEASONAL_QUERIES["summer"]))
    queries.extend(DISCOVERY_QUERIES[:2])
    gap_templates = {
        "mad": "restaurant café thy anbefaling",
        "natur": "vandretur nationalpark thy rute",
        "surf": "surf kursus cold hawaii",
        "born": "børneaktiviteter thy mors",
        "kultur": "udstilling koncert thy",
    }
    for cat in gap_categories[:2]:
        if cat in gap_templates:
            queries.append(gap_templates[cat])
    return queries[:6]
