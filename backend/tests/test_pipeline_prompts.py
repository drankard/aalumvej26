"""Every stage prompt must fully substitute — a leftover ${var} means a typo
between the prompt file and the stage that renders it."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas" / "content_pipeline"))

from stages import load_prompt  # noqa: E402

CASES = {
    "extract.md": dict(current_date="2026-07-20", season="summer",
                       existing_posts="- x", pages="### PAGE"),
    "judge.md": dict(current_date="2026-07-20", season="summer", closed_list="none",
                     existing_posts="- x", candidates="- y"),
    "write.md": dict(current_date="2026-07-20", season="summer", accepted="- z"),
    "source_judge.md": dict(current_date="2026-07-20", registry="- a.dk", candidates="### b.dk"),
    "area_audit.md": dict(current_date="2026-07-20", season="summer",
                          cards="### card", recent_posts="- p"),
}


@pytest.mark.parametrize("name,vars", CASES.items(), ids=list(CASES))
def test_prompt_fully_substitutes(name, vars):
    rendered = load_prompt(name, **vars)
    leftovers = re.findall(r"\$\{[a-z_]+\}", rendered)
    assert not leftovers, f"{name} has unsubstituted placeholders: {leftovers}"
    for value in vars.values():
        assert str(value) in rendered
