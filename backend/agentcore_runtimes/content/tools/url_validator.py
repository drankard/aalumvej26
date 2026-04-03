"""URL validation tool using httpx (same client as web_fetch)."""
import logging

import httpx
from strands import tool

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


@tool
def validate_url(url: str) -> dict:
    """Check if a URL is reachable and returns a valid response.

    Args:
        url: URL to validate

    Returns:
        Status code and whether the URL is valid
    """
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.head(url, headers=_HEADERS)
            if resp.status_code == 405:
                resp = client.get(url, headers=_HEADERS)
            return {"url": url, "valid": resp.status_code < 400, "status": resp.status_code}
    except httpx.TimeoutException:
        logger.warning(f"URL validation timeout: {url}")
        return {"url": url, "valid": False, "status": 0, "error": "timeout"}
    except Exception as e:
        logger.warning(f"URL validation failed: {url}: {e}")
        return {"url": url, "valid": False, "status": 0, "error": str(e)}
