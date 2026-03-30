"""Web search via DuckDuckGo HTML. No API key needed."""
import urllib.parse

import httpx
from bs4 import BeautifulSoup
from strands import tool

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


@tool
def search(query: str, max_results: int = 10, region: str = "dk-da") -> str:
    """Search the web using DuckDuckGo. Returns results with titles, URLs, and snippets.

    Args:
        query: Search query string. Be specific for better results (2-5 words).
        max_results: Maximum number of results to return (1-20, default 10).
        region: Region/language code for localized results. Default 'dk-da' for Danish. Examples: 'de-de' for German, 'wt-wt' for no region.

    Returns:
        Formatted search results with position, title, URL, and snippet.
    """
    data = {"q": query, "b": "", "kl": region, "kp": "-1"}

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post("https://html.duckduckgo.com/html", data=data, headers=_HEADERS)
            resp.raise_for_status()
    except Exception as e:
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
        return "No results found. Try rephrasing the query."

    lines = [f"Found {len(results)} results:\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   URL: {r['url']}")
        lines.append(f"   {r['snippet']}")
        lines.append("")
    return "\n".join(lines)
