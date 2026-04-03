"""Web search via DuckDuckGo HTML. No API key needed."""
import logging
import time
import urllib.parse

import httpx
from bs4 import BeautifulSoup
from strands import tool

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

_last_search_time = 0.0
_SEARCH_DELAY = 3.0
_consecutive_failures = 0
_MAX_CONSECUTIVE_FAILURES = 3


@tool
def search(query: str, max_results: int = 10, region: str = "dk-da") -> str:
    """Search the web using DuckDuckGo. Returns results with titles, URLs, and snippets.

    Rate-limited to one request every 3 seconds to avoid throttling.
    After 3 consecutive failures, stops accepting queries until next run.

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

    data = {"q": query, "b": "", "kl": region, "kp": "-1"}

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post("https://html.duckduckgo.com/html", data=data, headers=_HEADERS)
            _last_search_time = time.time()

            if resp.status_code == 202:
                _consecutive_failures += 1
                logger.warning(f"DuckDuckGo rate limited (202): query={query!r}, failures={_consecutive_failures}")
                return (
                    f"RATE LIMITED by DuckDuckGo (HTTP 202). "
                    f"Consecutive failures: {_consecutive_failures}/{_MAX_CONSECUTIVE_FAILURES}. "
                    f"Do NOT retry immediately — use fetch_content on known source URLs instead."
                )

            resp.raise_for_status()
    except Exception as e:
        _last_search_time = time.time()
        _consecutive_failures += 1
        logger.error(f"Search failed: query={query!r}, error={e}")
        return f"Search failed: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for r in soup.select(".result"):
        title_elem = r.select_one(".result__title")
        if not title_elem:
            continue
        link_elem = title_elem.find("a")
        if not link_elem:
            continue

        title = link_elem.get_text(strip=True)
        link = link_elem.get("href", "")

        if "y.js" in link:
            continue
        if link.startswith("//duckduckgo.com/l/?uddg="):
            link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])

        snippet_elem = r.select_one(".result__snippet")
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

        results.append({"title": title, "url": link, "snippet": snippet})
        if len(results) >= max_results:
            break

    if not results:
        _consecutive_failures += 1
        logger.warning(f"No results for query={query!r}, failures={_consecutive_failures}")
        return (
            f"No results found for: {query}. "
            f"Consecutive empty results: {_consecutive_failures}/{_MAX_CONSECUTIVE_FAILURES}."
        )

    _consecutive_failures = 0

    lines = [f"Found {len(results)} results:\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   URL: {r['url']}")
        lines.append(f"   {r['snippet']}")
        lines.append("")
    return "\n".join(lines)
