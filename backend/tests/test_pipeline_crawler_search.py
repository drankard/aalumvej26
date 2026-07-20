"""Tests for crawler (mock transport) and search providers (mock transport / env)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas" / "content_pipeline"))

from crawler import crawl, extract_text  # noqa: E402
from search import NullProvider, SerpApiProvider, build_queries, get_provider  # noqa: E402

HTML = """<html><head><style>.x{}</style></head><body>
<nav>Menu Home Kontakt</nav>
<main><h1>Krabbefest i Agger</h1><p>Lørdag 8. august 2026 ved De Sorte Huse.
Gratis adgang, fiskekonkurrence for børn kl. 10-14.</p></main>
<footer>Copyright</footer></body></html>"""


def test_extract_text_strips_chrome_keeps_content():
    text = extract_text(HTML)
    assert "Krabbefest i Agger" in text
    assert "8. august 2026" in text
    assert "Copyright" not in text


def test_extract_text_truncates():
    text = extract_text("<p>" + "word " * 5000 + "</p>", max_chars=100)
    assert len(text) <= 140
    assert "[truncated at 100 chars]" in text


def _transport(responses: dict[str, httpx.Response]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return responses.get(str(request.url), httpx.Response(404))
    return httpx.MockTransport(handler)


def test_crawl_mixed_outcomes():
    transport = _transport({
        "https://a.dk/events": httpx.Response(200, text=HTML),
        "https://b.dk/": httpx.Response(500),
    })
    results = crawl(
        [("a.dk", "https://a.dk/events"), ("b.dk", "https://b.dk/"), ("c.dk", "https://c.dk/x")],
        transport=transport,
    )
    by_url = {r.url: r for r in results}
    assert by_url["https://a.dk/events"].ok
    assert "Krabbefest" in by_url["https://a.dk/events"].text
    assert not by_url["https://b.dk/"].ok and by_url["https://b.dk/"].error == "HTTP 500"
    assert not by_url["https://c.dk/x"].ok and by_url["https://c.dk/x"].error == "HTTP 404"


def test_crawl_deadline_skips_remaining():
    transport = _transport({"https://a.dk/1": httpx.Response(200, text=HTML)})
    results = crawl([("a.dk", "https://a.dk/1"), ("a.dk", "https://a.dk/2")],
                    time_left=lambda: 0.0, transport=transport)
    assert all(not r.ok and "time budget" in (r.error or "") for r in results)


def test_serpapi_parses_organic_results():
    payload = {"organic_results": [
        {"title": "Thy360 kalender", "link": "https://thy360.dk/kalender", "snippet": "Det sker"},
        {"title": "No link ignored"},
    ]}
    with patch("search.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        resp = MagicMock()
        resp.json.return_value = payload
        client.get.return_value = resp
        hits = SerpApiProvider("k").search("events thy")
    assert len(hits) == 1
    assert hits[0].url == "https://thy360.dk/kalender"
    params = client.get.call_args.kwargs["params"]
    assert (params["gl"], params["hl"], params["google_domain"]) == ("dk", "da", "google.dk")


def test_serpapi_failure_returns_empty_never_raises():
    with patch("search.httpx.Client", side_effect=RuntimeError("boom")):
        assert SerpApiProvider("k").search("q") == []


def test_get_provider_none(monkeypatch):
    monkeypatch.setenv("SEARCH_PROVIDER", "none")
    assert isinstance(get_provider(), NullProvider)


def test_get_provider_missing_key_degrades_to_null(monkeypatch):
    monkeypatch.setenv("SEARCH_PROVIDER", "serpapi")
    ssm = MagicMock()
    ssm.get_parameter.side_effect = Exception("ParameterNotFound")
    assert isinstance(get_provider(ssm_client=ssm), NullProvider)


def test_get_provider_with_key(monkeypatch):
    monkeypatch.setenv("SEARCH_PROVIDER", "serpapi")
    ssm = MagicMock()
    ssm.get_parameter.return_value = {"Parameter": {"Value": "secret"}}
    assert isinstance(get_provider(ssm_client=ssm), SerpApiProvider)


def test_build_queries_bounded_and_seasonal():
    q = build_queries("autumn", ["mad", "surf", "born"])
    assert len(q) <= 6
    assert any("efterår" in x or "østers" in x for x in q)
    assert any("restaurant" in x for x in q)  # gap category included
    assert "børneaktiviteter thy mors" not in q  # only first 2 gaps
