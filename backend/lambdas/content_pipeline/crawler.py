"""Parallel crawler: polite per-domain, hard timeouts, main-content extraction.

Domains run concurrently; requests within one domain run sequentially with a
delay. A deadline callable caps total crawl time — when it expires, remaining
fetches are marked skipped (never silently dropped).
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Callable

import httpx

from schemas import CrawlResult

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 aalumvej26-bot"
}
FETCH_TIMEOUT = 15.0
PER_DOMAIN_DELAY = 1.0
MAX_CONCURRENT_DOMAINS = 8
DEFAULT_MAX_CHARS = 5000


def extract_text(html: str, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """Main-content extraction via trafilatura, falling back to a tag-strip."""
    text = None
    try:
        import trafilatura
        text = trafilatura.extract(html, include_comments=False, include_tables=True)
    except Exception:  # pragma: no cover - trafilatura internal failure
        text = None

    if not text:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for el in soup(["script", "style", "nav", "header", "footer", "noscript"]):
            el.decompose()
        text = soup.get_text(" ")

    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars] + f" [truncated at {max_chars} chars]"
    return text


async def _fetch_one(client: httpx.AsyncClient, domain: str, url: str, max_chars: int) -> CrawlResult:
    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=FETCH_TIMEOUT)
        if resp.status_code >= 400:
            return CrawlResult(domain=domain, url=url, ok=False, status=resp.status_code,
                               error=f"HTTP {resp.status_code}")
        return CrawlResult(domain=domain, url=url, ok=True, status=resp.status_code,
                           text=extract_text(resp.text, max_chars))
    except httpx.TimeoutException:
        return CrawlResult(domain=domain, url=url, ok=False, error="timeout")
    except Exception as e:
        return CrawlResult(domain=domain, url=url, ok=False, error=f"{type(e).__name__}: {e}")


async def _crawl_domain(
    client: httpx.AsyncClient,
    domain: str,
    urls: list[str],
    max_chars: int,
    time_left: Callable[[], float],
    sem: asyncio.Semaphore,
) -> list[CrawlResult]:
    results = []
    async with sem:
        for i, url in enumerate(urls):
            if time_left() <= 0:
                results.append(CrawlResult(domain=domain, url=url, ok=False,
                                           error="skipped: crawl time budget exhausted"))
                continue
            if i > 0:
                await asyncio.sleep(PER_DOMAIN_DELAY)
            results.append(await _fetch_one(client, domain, url, max_chars))
    return results


async def _crawl_async(
    targets: list[tuple[str, str]],
    max_chars: int,
    time_left: Callable[[], float],
) -> list[CrawlResult]:
    by_domain: dict[str, list[str]] = {}
    for domain, url in targets:
        by_domain.setdefault(domain, []).append(url)

    sem = asyncio.Semaphore(MAX_CONCURRENT_DOMAINS)
    async with httpx.AsyncClient() as client:
        groups = await asyncio.gather(*[
            _crawl_domain(client, domain, urls, max_chars, time_left, sem)
            for domain, urls in by_domain.items()
        ])
    return [r for group in groups for r in group]


def crawl(
    targets: list[tuple[str, str]],
    max_chars: int = DEFAULT_MAX_CHARS,
    time_left: Callable[[], float] = lambda: 3600.0,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[CrawlResult]:
    """Crawl (domain, url) targets. `transport` is injectable for tests."""
    if transport is not None:
        async def _with_transport() -> list[CrawlResult]:
            by_domain: dict[str, list[str]] = {}
            for domain, url in targets:
                by_domain.setdefault(domain, []).append(url)
            sem = asyncio.Semaphore(MAX_CONCURRENT_DOMAINS)
            async with httpx.AsyncClient(transport=transport) as client:
                groups = await asyncio.gather(*[
                    _crawl_domain(client, domain, urls, max_chars, time_left, sem)
                    for domain, urls in by_domain.items()
                ])
            return [r for group in groups for r in group]
        return asyncio.run(_with_transport())
    return asyncio.run(_crawl_async(targets, max_chars, time_left))


def validate_url(url: str, timeout: float = 10.0) -> bool:
    """Pre-publish reachability gate (sync, single URL)."""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.head(url, headers=HEADERS)
            if resp.status_code == 405:
                resp = client.get(url, headers=HEADERS)
            return resp.status_code < 400
    except Exception:
        return False
