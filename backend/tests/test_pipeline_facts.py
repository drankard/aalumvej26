"""Provenance gate on the facts table.

Every fact row published on the site is a claim about somebody else's business —
their opening hours, their prices, their age limits. A row survives only if it
came from a crawled source or the site derived it itself; anything else is the
model guessing, and a guess in three languages is worse than an empty table.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas" / "content_pipeline"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas import MAX_FACTS, MAX_FAQ, TranslationEntry, drop_unsourced_facts  # noqa: E402
from stages import merge_translations  # noqa: E402

SOURCED = {"label": "Højde", "value": "35 meter", "source_url": "https://nationalparkthy.dk/x"}
COMPUTED = {"label": "Afstand", "value": "18 km", "computed": True}
GUESSED = {"label": "Pris", "value": "ca. 30 kr."}


def entry(**over) -> TranslationEntry:
    base = dict(title="t", excerpt="e", date="d")
    base.update(over)
    return TranslationEntry(**base)


def test_sourced_fact_is_kept():
    assert entry(facts=[SOURCED]).facts[0].value == "35 meter"


def test_site_computed_fact_is_kept_without_a_source_url():
    kept = entry(facts=[COMPUTED]).facts
    assert len(kept) == 1 and kept[0].computed is True


def test_unsourced_fact_is_dropped():
    assert entry(facts=[GUESSED]).facts == []


def test_one_bad_row_does_not_cost_the_whole_post():
    kept = entry(facts=[SOURCED, GUESSED, COMPUTED]).facts
    assert [f.label for f in kept] == ["Højde", "Afstand"]


@pytest.mark.parametrize("url", ["", "   ", "nationalparkthy.dk", "javascript:alert(1)", "/relative"])
def test_source_url_must_be_absolute_http(url):
    assert entry(facts=[{**GUESSED, "source_url": url}]).facts == []


def test_rows_missing_label_or_value_are_dropped():
    rows = [{"label": "", "value": "x", "source_url": "https://a.dk"},
            {"label": "y", "value": "", "source_url": "https://a.dk"}]
    assert entry(facts=rows).facts == []


def test_facts_are_capped():
    kept = entry(facts=[dict(SOURCED, label=f"l{i}") for i in range(MAX_FACTS + 5)]).facts
    assert len(kept) == MAX_FACTS


def test_faq_is_capped():
    items = [{"question": f"q{i}", "answer": "a"} for i in range(MAX_FAQ + 3)]
    assert len(entry(faq=items).faq) == MAX_FAQ


def test_drop_unsourced_reports_how_many_it_removed():
    kept, dropped = drop_unsourced_facts([SOURCED, GUESSED, GUESSED])
    assert len(kept) == 1 and dropped == 2


def test_depth_fields_are_optional():
    """Copy written before the expansion must still validate."""
    e = entry()
    assert (e.tldr, e.body, e.facts, e.faq) == ("", "", [], [])


class TestPreservedFields:
    """`from_house` is hand-written and must survive automated rewrites."""

    def test_hand_written_note_survives_an_area_rewrite(self):
        existing = {"da": {"name": "Agger", "desc": "old", "from_house": "Vi cykler derud."}}
        incoming = {"da": {"name": "Agger", "desc": "new"}}
        assert merge_translations(existing, incoming)["da"]["from_house"] == "Vi cykler derud."

    def test_rewritten_copy_still_replaces_the_generated_fields(self):
        existing = {"da": {"desc": "old", "from_house": "note"}}
        incoming = {"da": {"desc": "new"}}
        assert merge_translations(existing, incoming)["da"]["desc"] == "new"

    def test_an_explicit_new_value_wins(self):
        existing = {"da": {"from_house": "old note"}}
        incoming = {"da": {"from_house": "new note"}}
        assert merge_translations(existing, incoming)["da"]["from_house"] == "new note"

    def test_languages_absent_from_the_rewrite_are_not_invented(self):
        merged = merge_translations({"da": {"from_house": "x"}, "en": {"from_house": "y"}},
                                    {"da": {"desc": "new"}})
        assert set(merged) == {"da"}
