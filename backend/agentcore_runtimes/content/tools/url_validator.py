"""URL validation tool."""
import urllib.request
import urllib.error

from strands import tool


@tool
def validate_url(url: str) -> dict:
    """Check if a URL is reachable and returns a valid response.

    Args:
        url: URL to validate

    Returns:
        Status code and whether the URL is valid
    """
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Aalumvej26-ContentAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"url": url, "valid": resp.status < 400, "status": resp.status}
    except urllib.error.HTTPError as e:
        return {"url": url, "valid": e.code < 400, "status": e.code}
    except Exception as e:
        return {"url": url, "valid": False, "status": 0, "error": str(e)}
