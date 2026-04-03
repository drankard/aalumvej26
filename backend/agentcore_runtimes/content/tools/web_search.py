"""Web search via DuckDuckGo using the ddgs library with browser fingerprint impersonation."""
import logging
import time

from ddgs import DDGS
from strands import tool

logger = logging.getLogger(__name__)

_last_search_time = 0.0
_SEARCH_DELAY = 2.0
_consecutive_failures = 0
_MAX_CONSECUTIVE_FAILURES = 5


@tool
def search(query: str, max_results: int = 10, region: str = "dk-da") -> str:
    """Search the web using DuckDuckGo. Returns results with titles, URLs, and snippets.

    Uses browser TLS fingerprint impersonation to avoid rate limiting.
    After 5 consecutive failures, stops accepting queries until next run.

    Args:
        query: Search query string. Be specific for better results (2-5 words).
        max_results: Maximum number of results to return (1-20, default 10).
        region: Region/language code for localized results. Default 'dk-da' for Danish.

    Returns:
        Formatted search results with position, title, URL, and snippet.
    """
    global _last_search_time, _consecutive_failures

    if _consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
        return (
            f"SEARCH UNAVAILABLE: DuckDuckGo has rate-limited this session "
            f"({_consecutive_failures} consecutive failures). "
            f"Stop searching and work with the content you already have."
        )

    elapsed = time.time() - _last_search_time
    if elapsed < _SEARCH_DELAY:
        time.sleep(_SEARCH_DELAY - elapsed)

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, region=region, max_results=max_results))
        _last_search_time = time.time()
    except Exception as e:
        _last_search_time = time.time()
        _consecutive_failures += 1
        error_msg = str(e).lower()
        if "ratelimit" in error_msg or "202" in error_msg:
            logger.warning(f"DuckDuckGo rate limited: query={query!r}, failures={_consecutive_failures}")
            return (
                f"RATE LIMITED by DuckDuckGo. "
                f"Consecutive failures: {_consecutive_failures}/{_MAX_CONSECUTIVE_FAILURES}. "
                f"Do NOT retry immediately — use fetch_content on known source URLs instead."
            )
        logger.error(f"Search failed: query={query!r}, error={e}")
        return f"Search failed: {e}"

    if not raw_results:
        _consecutive_failures += 1
        logger.warning(f"No results for query={query!r}, failures={_consecutive_failures}")
        return (
            f"No results found for: {query}. "
            f"Consecutive empty results: {_consecutive_failures}/{_MAX_CONSECUTIVE_FAILURES}."
        )

    _consecutive_failures = 0

    lines = [f"Found {len(raw_results)} results:\n"]
    for i, r in enumerate(raw_results, 1):
        lines.append(f"{i}. {r.get('title', '')}")
        lines.append(f"   URL: {r.get('href', '')}")
        lines.append(f"   {r.get('body', '')}")
        lines.append("")
    return "\n".join(lines)
