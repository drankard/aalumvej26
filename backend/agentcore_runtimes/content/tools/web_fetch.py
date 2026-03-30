"""Fetch and extract text content from web pages. No API key needed."""
import re

import httpx
from bs4 import BeautifulSoup
from strands import tool

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


@tool
def fetch_content(url: str, max_length: int = 8000) -> str:
    """Fetch and extract the main text content from a webpage. Strips navigation, headers, footers, scripts, and styles.

    Args:
        url: Full URL to fetch (must start with http:// or https://).
        max_length: Maximum characters to return (default 8000).

    Returns:
        Cleaned text content from the page.
    """
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            resp = client.get(url, headers=_HEADERS)
            resp.raise_for_status()
    except Exception as e:
        return f"Error fetching {url}: {e}"

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
