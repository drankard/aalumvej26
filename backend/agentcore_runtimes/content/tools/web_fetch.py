"""Web fetch tool for crawling source pages."""
import urllib.request
import urllib.error
from html.parser import HTMLParser

from strands import tool


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._text: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self._text.append(stripped)

    def get_text(self) -> str:
        return "\n".join(self._text)


@tool
def web_fetch(url: str, max_chars: int = 5000) -> dict:
    """Fetch a web page and extract its text content.

    Args:
        url: URL to fetch
        max_chars: Maximum characters to return (default 5000)

    Returns:
        Extracted text content and metadata
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Aalumvej26-ContentAgent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            parser = _TextExtractor()
            parser.feed(html)
            text = parser.get_text()[:max_chars]
            return {"url": url, "status": resp.status, "text": text, "truncated": len(parser.get_text()) > max_chars}
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "error": str(e), "text": ""}
    except Exception as e:
        return {"url": url, "status": 0, "error": str(e), "text": ""}
