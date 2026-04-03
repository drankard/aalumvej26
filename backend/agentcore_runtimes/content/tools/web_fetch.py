"""Fetch and extract text content from web pages. No API key needed."""
import logging
import re
import time

import httpx
from bs4 import BeautifulSoup
from strands import tool

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

_last_fetch_time = 0.0
_FETCH_DELAY = 2.0


@tool
def fetch_content(url: str, max_length: int = 2000) -> str:
    """Fetch and extract the main text content from a webpage. Strips navigation, headers, footers, scripts, and styles.

    Rate-limited to one request every 2 seconds to be polite to sources.

    Args:
        url: Full URL to fetch (must start with http:// or https://).
        max_length: Maximum characters to return (default 2000).

    Returns:
        Cleaned text content from the page, or a clear error message with HTTP status.
    """
    global _last_fetch_time

    elapsed = time.time() - _last_fetch_time
    if elapsed < _FETCH_DELAY:
        time.sleep(_FETCH_DELAY - elapsed)

    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            resp = client.get(url, headers=_HEADERS)
            _last_fetch_time = time.time()

            if resp.status_code == 404:
                logger.warning(f"404 Not Found: {url}")
                return f"FAILED: {url} returned 404 Not Found. This URL is broken — do not use it."

            if resp.status_code >= 400:
                logger.warning(f"HTTP {resp.status_code}: {url}")
                return f"FAILED: {url} returned HTTP {resp.status_code}. Do not use this URL."

            resp.raise_for_status()
    except httpx.TimeoutException:
        _last_fetch_time = time.time()
        logger.error(f"Timeout fetching {url}")
        return f"FAILED: {url} timed out after 30 seconds."
    except Exception as e:
        _last_fetch_time = time.time()
        logger.error(f"Error fetching {url}: {e}")
        return f"FAILED: Could not fetch {url}: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")
    for el in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        el.decompose()

    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = " ".join(chunk for chunk in chunks if chunk)
    text = re.sub(r"\s+", " ", text).strip()

    total = len(text)
    text = text[:max_length]
    if total > max_length:
        text += f"\n\n[Truncated: showing {max_length} of {total} characters]"

    return text
