"""Depth backfill: adding tldr/body/facts/faq to already-published posts.

The write stage only ever creates new posts, so without this the pages that are
already indexed keep empty depth fields forever — the whole content investment
sits dormant on exactly the URLs that matter most.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas" / "content_pipeline"))

import stages as st  # noqa: E402
from stages import RunState, posts_missing_depth, stage_backfill_depth  # noqa: E402


def _post(pid, title, *, tldr="", from_house="", status="published"):
    tr = {
        lang: {"title": title, "excerpt": "kort", "date": "d", "tldr": tldr,
               "from_house": from_house}
        for lang in ("da", "en", "de")
    }
    return {"pk": "POST", "sk": f"POST#{pid}", "id": pid, "status": status,
            "url": f"https://kilde.dk/{pid}", "tag_key": "guide",
            "translations": tr}


class FakeTable:
    def __init__(self):
        self.updates = []

    def update_item(self, **kwargs):
        self.updates.append(kwargs)


class FakeBedrock:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def converse(self, modelId, messages, toolConfig, inferenceConfig):
        self.calls += 1
        name = toolConfig["toolChoice"]["tool"]["name"]
        return {"output": {"message": {"role": "assistant", "content": [
            {"toolUse": {"toolUseId": "t", "name": name, "input": self.payload}}]}}}


def _depth_payload(title, facts):
    return {"posts": [{
        "title_ref": title,
        "translations": {
            lang: {"tldr": "Kort svar.", "body": "## H\n\nTekst.",
                   "facts": facts, "faq": [{"question": "Q?", "answer": "A."}]}
            for lang in ("da", "en", "de")
        },
    }]}


@pytest.fixture
def state():
    import datetime
    return RunState(pipeline="oplevelser", today=datetime.date(2026, 8, 1),
                    season="summer", model_id="fake")


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """The stage crawls each post's own source; keep that offline."""
    monkeypatch.setattr(st, "crawl", lambda targets, time_left=None: [])


class TestSelection:
    def test_published_post_without_tldr_is_selected(self):
        assert len(posts_missing_depth([_post("a", "A")])) == 1

    def test_post_that_already_has_depth_is_left_alone(self):
        assert posts_missing_depth([_post("a", "A", tldr="allerede")]) == []

    def test_archived_posts_are_ignored(self):
        assert posts_missing_depth([_post("a", "A", status="archived")]) == []

    def test_body_is_not_the_marker(self):
        """Dated events legitimately have an empty body; keying off it would
        reprocess every event on every run, forever."""
        p = _post("a", "A", tldr="har tldr")
        for lang in ("da", "en", "de"):
            p["translations"][lang]["body"] = ""
        assert posts_missing_depth([p]) == []


class TestBackfill:
    def test_depth_is_written_to_the_existing_post(self, state):
        state.posts = [_post("a", "Lodbjerg Fyr")]
        table = FakeTable()
        bedrock = FakeBedrock(_depth_payload("Lodbjerg Fyr", [
            {"label": "Hoejde", "value": "35 m", "source_url": "https://kilde.dk/a"}]))

        stage_backfill_depth(state, table, bedrock)

        assert len(table.updates) == 1
        tr = table.updates[0]["ExpressionAttributeValues"][":t"]
        assert tr["da"]["tldr"] == "Kort svar."
        assert tr["da"]["facts"][0]["value"] == "35 m"
        assert state.depth_filled == ["Lodbjerg Fyr"]

    def test_unsourced_fact_never_reaches_the_table(self, state):
        state.posts = [_post("a", "Lodbjerg Fyr")]
        table = FakeTable()
        bedrock = FakeBedrock(_depth_payload("Lodbjerg Fyr", [
            {"label": "Hoejde", "value": "35 m", "source_url": "https://kilde.dk/a"},
            {"label": "Pris", "value": "ca. 30 kr."},
        ]))

        stage_backfill_depth(state, table, bedrock)

        labels = [f["label"] for f in
                  table.updates[0]["ExpressionAttributeValues"][":t"]["da"]["facts"]]
        assert labels == ["Hoejde"]

    def test_published_title_excerpt_and_date_are_untouched(self, state):
        state.posts = [_post("a", "Lodbjerg Fyr")]
        table = FakeTable()
        stage_backfill_depth(state, table, FakeBedrock(_depth_payload("Lodbjerg Fyr", [])))

        da = table.updates[0]["ExpressionAttributeValues"][":t"]["da"]
        assert (da["title"], da["excerpt"], da["date"]) == ("Lodbjerg Fyr", "kort", "d")

    def test_hand_written_from_house_survives(self, state):
        state.posts = [_post("a", "Lodbjerg Fyr", from_house="Vi koerer derud sidst paa dagen.")]
        table = FakeTable()
        stage_backfill_depth(state, table, FakeBedrock(_depth_payload("Lodbjerg Fyr", [])))

        tr = table.updates[0]["ExpressionAttributeValues"][":t"]
        assert tr["da"]["from_house"] == "Vi koerer derud sidst paa dagen."

    def test_unmatched_title_is_reported_not_applied(self, state):
        state.posts = [_post("a", "Lodbjerg Fyr")]
        table = FakeTable()
        stage_backfill_depth(state, table, FakeBedrock(_depth_payload("Et andet sted", [])))

        assert table.updates == []
        assert any("no post matched" in n for n in state.notes)

    def test_nothing_pending_makes_no_model_call(self, state):
        state.posts = [_post("a", "A", tldr="har depth")]
        bedrock = FakeBedrock(_depth_payload("A", []))
        stage_backfill_depth(state, FakeTable(), bedrock)
        assert bedrock.calls == 0

    def test_batch_is_capped_and_remainder_reported(self, state):
        state.posts = [_post(str(i), f"P{i}") for i in range(st.DEPTH_PER_RUN + 3)]
        table = FakeTable()
        stage_backfill_depth(state, table, FakeBedrock(_depth_payload("P0", [])))
        assert any("still pending" in n for n in state.notes)

    def test_model_failure_does_not_abort_the_run(self, state):
        """A run that just published new content must still reach its report."""
        class Exploding(FakeBedrock):
            def converse(self, **kwargs):
                raise RuntimeError("bedrock down")

        state.posts = [_post("a", "Lodbjerg Fyr")]
        table = FakeTable()
        stage_backfill_depth(state, table, Exploding({}))

        assert table.updates == []
        assert any("Depth backfill: skipped" in n for n in state.notes)
