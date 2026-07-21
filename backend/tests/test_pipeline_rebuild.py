"""Rebuild-trigger tests: after a successful run the pipeline kicks the
CodeBuild project that regenerates the static site. The trigger must be a
no-op when unconfigured and must never fail the content run."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas" / "content_pipeline"))

import app  # noqa: E402


class FakeCodeBuild:
    def __init__(self, fail: bool = False):
        self.calls: list[str] = []
        self.fail = fail

    def start_build(self, projectName: str):
        self.calls.append(projectName)
        if self.fail:
            raise RuntimeError("boom")
        return {"build": {"id": f"{projectName}:0123abcd"}}


class FakeSession:
    def __init__(self, codebuild: FakeCodeBuild):
        self._codebuild = codebuild

    def client(self, name, **_):
        assert name == "codebuild", f"unexpected client {name}"
        return self._codebuild


def test_skipped_when_unconfigured(monkeypatch):
    monkeypatch.delenv("CONTENT_REBUILD_PROJECT", raising=False)
    codebuild = FakeCodeBuild()
    msg = app._trigger_rebuild(FakeSession(codebuild))
    assert "skipped" in msg
    assert codebuild.calls == []


def test_triggers_configured_project(monkeypatch):
    monkeypatch.setenv("CONTENT_REBUILD_PROJECT", "aalumvej26-content-rebuild-prod")
    codebuild = FakeCodeBuild()
    msg = app._trigger_rebuild(FakeSession(codebuild))
    assert codebuild.calls == ["aalumvej26-content-rebuild-prod"]
    assert "triggered" in msg
    assert "0123abcd" in msg  # build id surfaces in the report


def test_trigger_failure_reports_but_never_raises(monkeypatch):
    monkeypatch.setenv("CONTENT_REBUILD_PROJECT", "aalumvej26-content-rebuild-prod")
    msg = app._trigger_rebuild(FakeSession(FakeCodeBuild(fail=True)))
    assert "FAILED" in msg
    assert "boom" in msg
