"""End-to-end pipeline test: the real app.lambda_handler with faked AWS edges.

In-memory DynamoDB table, scripted Bedrock converse, mocked crawler/network.
Verifies the complete oplevelser flow (seed → archive → crawl → extract →
filter → judge → write → publish → report) and the omraadet audit flow.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas" / "content_pipeline"))

from schemas import CrawlResult  # noqa: E402


# ---------- fakes ----------

class FakeTable:
    def __init__(self):
        self.items: dict[tuple[str, str], dict] = {}

    def seed(self, item: dict) -> None:
        self.items[(item["pk"], item["sk"])] = item

    def query(self, **kwargs):
        pk = kwargs["ExpressionAttributeValues"][":pk"]
        items = [dict(v) for (p, _), v in sorted(self.items.items()) if p == pk]
        return {"Items": items}

    def put_item(self, Item):
        self.items[(Item["pk"], Item["sk"])] = dict(Item)

    def update_item(self, Key, UpdateExpression, ExpressionAttributeValues,
                    ExpressionAttributeNames=None, **_):
        item = self.items[(Key["pk"], Key["sk"])]
        vals = ExpressionAttributeValues
        if ":s" in vals:
            item["status"] = vals[":s"]
        if ":t" in vals:
            item["translations"] = vals[":t"]
        if ":url" in vals:
            item["url"] = vals[":url"]
        if ":u" in vals:
            item["updated_at"] = vals[":u"]

    def posts(self, status=None):
        out = [v for (p, _), v in self.items.items() if p == "POST"]
        return [p for p in out if status is None or p["status"] == status]


class FakeBedrock:
    """Returns scripted tool inputs keyed by the forced tool name."""

    def __init__(self, scripts: dict[str, list[dict] | dict]):
        self.scripts = {k: (v if isinstance(v, list) else [v]) for k, v in scripts.items()}
        self.calls: list[str] = []

    def converse(self, modelId, messages, toolConfig, inferenceConfig):
        name = toolConfig["toolChoice"]["tool"]["name"]
        self.calls.append(name)
        queue = self.scripts[name]
        payload = queue.pop(0) if len(queue) > 1 else queue[0]
        return {"output": {"message": {"role": "assistant", "content": [
            {"toolUse": {"toolUseId": "t", "name": name, "input": payload}}]}}}


class FakeSNS:
    def __init__(self):
        self.published: list[tuple[str, str]] = []

    def publish(self, TopicArn, Subject, Message):
        self.published.append((Subject, Message))


class FakeSession:
    def __init__(self, table, bedrock, sns):
        self._table, self._bedrock, self._sns = table, bedrock, sns

    def resource(self, name, **_):
        assert name == "dynamodb"
        table = self._table
        return type("R", (), {"Table": staticmethod(lambda _n: table)})()

    def client(self, name, **_):
        if name == "bedrock-runtime":
            return self._bedrock
        if name == "sns":
            return self._sns
        raise AssertionError(f"unexpected client {name}")


class FakeContext:
    def get_remaining_time_in_millis(self):
        return 800_000


# ---------- fixtures ----------

TR = {"da": {"title": "t", "excerpt": "e", "date": "d"},
      "en": {"title": "t", "excerpt": "e", "date": "d"},
      "de": {"title": "t", "excerpt": "e", "date": "d"}}


def _existing_post(pid, title, status="published", **extra):
    tr = {lang: {**TR[lang], "title": title} for lang in TR}
    return {"pk": "POST", "sk": f"POST#{pid}", "id": pid, "status": status,
            "category": "kultur", "tag_key": "event", "url": f"https://old.dk/{pid}",
            "emoji": "🎵", "sort_order": 1, "translations": tr, **extra}


def _area(aid, name, url):
    return {"pk": "AREA", "sk": f"AREA#{aid}", "id": aid, "status": "published", "url": url,
            "translations": {"da": {"name": name, "dist": "~20 min", "desc": "God tur."},
                             "en": {"name": name, "dist": "~20 min", "desc": "Nice."},
                             "de": {"name": name, "dist": "~20 Min", "desc": "Schön."}}}


GOOD_COPY = {
    "title_ref": "Sommerkoncert i Agger", "category": "kultur", "tag_key": "event",
    "url": "https://ny.dk/koncert", "emoji": "🎵",
    "event_start": "2026-08-01", "event_end": "2026-08-01",
    "translations": {
        "da": {"title": "Sommerkoncert i Agger", "excerpt": "Koncert ved De Sorte Huse kl. 20. Gratis.", "date": "1. august 2026"},
        "en": {"title": "Summer concert in Agger", "excerpt": "Concert at De Sorte Huse, 8 PM. Free.", "date": "1 August 2026"},
        "de": {"title": "Sommerkonzert in Agger", "excerpt": "Konzert bei De Sorte Huse, 20 Uhr. Gratis.", "date": "1. August 2026"},
    },
}

SCRIPTS = {
    "record_candidates": {"candidates": [
        {"title": "Sommerkoncert i Agger", "event_start": "2026-08-01", "event_end": "2026-08-01",
         "location": "Agger", "source_url": "https://ny.dk/koncert", "source_domain": "ny.dk",
         "category": "kultur", "details": "Kl. 20, gratis, De Sorte Huse."},
        {"title": "Gammel Fest", "event_start": "2027-01-01", "event_end": "2027-01-02",
         "location": "Thisted", "source_url": "https://x.dk/y", "category": "kultur",
         "details": "Langt ude i fremtiden."},
        {"title": "Krabbefest i Agger", "event_start": "2026-08-08", "event_end": "2026-08-08",
         "location": "Agger", "source_url": "https://old.dk/keep", "category": "born",
         "details": "Duplicate af eksisterende."},
    ]},
    "record_judgments": {"judgments": [
        {"title": "Sommerkoncert i Agger", "accept": True, "score": 9, "reason": "Local, free, dated."},
    ]},
    "record_posts": {"posts": [GOOD_COPY]},
    "record_audits": {"audits": [], "new_card_recommendations": []},
}


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("MODEL_ID", "fake-model")
    monkeypatch.setenv("SEARCH_PROVIDER", "none")
    monkeypatch.setenv("SNS_TOPIC_ARN", "arn:aws:sns:eu-west-1:1:fake")
    monkeypatch.setenv("TABLE_NAME", "fake")


def _wire(monkeypatch, table, bedrock, crawl_results):
    import app
    import stages as st
    sns = FakeSNS()
    session = FakeSession(table, bedrock, sns)
    monkeypatch.setattr(app.boto3, "Session", lambda: session)
    monkeypatch.setattr(st, "crawl", lambda targets, **kw: list(crawl_results))
    monkeypatch.setattr(st, "validate_url", lambda url, **kw: "dead" not in url)
    return app, sns


# ---------- tests ----------

def test_oplevelser_end_to_end(env, monkeypatch):
    table = FakeTable()
    table.seed(_existing_post("expired1", "Forårsfest", event_start="2026-05-01", event_end="2026-05-02"))
    table.seed(_existing_post("keep1", "Krabbefest i Agger 2026", event_start=None, event_end=None,
                              url="https://old.dk/keep"))

    bedrock = FakeBedrock(dict(SCRIPTS))
    crawl_results = [
        CrawlResult(domain="aggerdarling.dk", url="https://www.aggerdarling.dk/", ok=True,
                    text="Sommerkoncert 1. august kl 20 De Sorte Huse gratis"),
        CrawlResult(domain="visitthy.com", url="https://www.visitthy.com/x", ok=False, error="HTTP 455"),
    ]
    app, sns = _wire(monkeypatch, table, bedrock, crawl_results)

    result = app.lambda_handler({"pipeline": "oplevelser"}, FakeContext())

    # published + archived counts surface in the return value
    assert result["published"] == 1
    assert result["archived"] == 1

    # registry auto-seeded
    sources = [v for (p, _), v in table.items.items() if p == "SOURCE"]
    assert len(sources) == 44

    # expired post archived; new post live with machine dates + run_id
    assert table.items[("POST", "POST#expired1")]["status"] == "archived"
    new = [p for p in table.posts("published") if p.get("run_id")]
    assert len(new) == 1
    assert new[0]["event_start"] == "2026-08-01"
    assert new[0]["translations"]["de"]["title"] == "Sommerkonzert in Agger"
    assert new[0]["sort_order"] == 1

    # run row is truthful: 3 extracted, 2 filtered out (too_far_future + duplicate)
    runs = [v for (p, _), v in table.items.items() if p == "PIPELINE_RUN"]
    assert len(runs) == 1
    assert runs[0]["candidates_found"] == 3
    assert runs[0]["published"] == 1
    assert runs[0]["rejections"] == {"too_far_future": 1, "duplicate": 1}
    assert runs[0]["error"] == ""
    assert runs[0]["run_id"] == result["run_id"]

    # email sent, truthful, single
    assert len(sns.published) == 1
    subject, body = sns.published[0]
    assert subject == "[aalumvej26] oplevelser: 1 new, 1 archived"
    assert "Sommerkoncert i Agger" in body
    assert "Forårsfest" in body
    assert "seeded" in body  # first-run seeding note
    assert "visitthy.com" in body  # failed domain reported

    # model called exactly three times: extract, judge, write
    assert bedrock.calls == ["record_candidates", "record_judgments", "record_posts"]

    # source health recorded for crawled domains
    darling = table.items[("SOURCE", "aggerdarling.dk")]
    assert darling["consecutive_failures"] == 0 and darling["last_success"]
    visitthy = table.items[("SOURCE", "visitthy.com")]
    assert visitthy["consecutive_failures"] == 1 and visitthy["status"] == "failing"


def test_oplevelser_failure_still_reports_and_raises(env, monkeypatch):
    table = FakeTable()
    bedrock = FakeBedrock({"record_candidates": {"candidates": []}})

    class ExplodingBedrock(FakeBedrock):
        def converse(self, *a, **k):
            raise RuntimeError("bedrock down")

    app, sns = _wire(monkeypatch, table, ExplodingBedrock({}), [
        CrawlResult(domain="aggerdarling.dk", url="https://www.aggerdarling.dk/", ok=True, text="x")])

    with pytest.raises(RuntimeError, match="bedrock down"):
        app.lambda_handler({"pipeline": "oplevelser"}, FakeContext())

    # even on crash: run row written with error + email flagged FAILED
    runs = [v for (p, _), v in table.items.items() if p == "PIPELINE_RUN"]
    assert len(runs) == 1 and "bedrock down" in runs[0]["error"]
    assert len(sns.published) == 1
    assert "FAILED" in sns.published[0][0]
    assert "RUN FAILED" in sns.published[0][1]


def test_omraadet_end_to_end(env, monkeypatch):
    table = FakeTable()
    table.seed(_area("a1", "Nationalpark Thy", "https://nationalparkthy.dk/"))
    table.seed(_area("a2", "Død Attraktion", "https://dead.dk/page"))

    new_tr = {"da": {"name": "Nationalpark Thy", "dist": "Omgiver Agger", "desc": "Opdateret åbningstid 10-17."},
              "en": {"name": "Thy National Park", "dist": "Surrounds Agger", "desc": "Updated hours 10-17."},
              "de": {"name": "Nationalpark Thy", "dist": "Umgibt Agger", "desc": "Neue Zeiten 10-17."}}
    bedrock = FakeBedrock({
        "record_audits": {"audits": [
            {"area_id": "a1", "verdict": "minor_update", "reasoning": "Hours changed on site.",
             "url": None, "translations": new_tr},
            {"area_id": "a2", "verdict": "broken_link", "reasoning": "Page gone.",
             "url": None, "translations": None},
        ], "new_card_recommendations": ["Stenbjerg Landingsplads — appears in 4 recent posts"]},
    })
    crawl_results = [
        CrawlResult(domain="nationalparkthy.dk", url="https://nationalparkthy.dk/", ok=True, text="Åbent 10-17"),
        CrawlResult(domain="dead.dk", url="https://dead.dk/page", ok=False, error="HTTP 404"),
    ]
    app, sns = _wire(monkeypatch, table, bedrock, crawl_results)

    result = app.lambda_handler({"pipeline": "omraadet"}, FakeContext())
    assert result["pipeline"] == "omraadet"

    # area updated in place, all languages
    assert table.items[("AREA", "AREA#a1")]["translations"] == new_tr

    subject, body = sns.published[0]
    assert "1 areas updated" in subject
    assert "BROKEN LINK" in body
    assert "Stenbjerg" in body
