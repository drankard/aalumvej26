"""Tests for the structured-output LLM wrapper (mocked Bedrock client)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambdas" / "content_pipeline"))

from llm import call_structured  # noqa: E402


class Out(BaseModel):
    value: int


def _response(tool_input: dict) -> dict:
    return {"output": {"message": {
        "role": "assistant",
        "content": [{"toolUse": {"toolUseId": "t1", "name": "record_result", "input": tool_input}}],
    }}}


def test_valid_first_attempt():
    client = MagicMock()
    client.converse.return_value = _response({"value": 7})
    out = call_structured(client, "model-x", "prompt", Out)
    assert out.value == 7
    assert client.converse.call_count == 1
    # forced tool choice
    kwargs = client.converse.call_args.kwargs
    assert kwargs["toolConfig"]["toolChoice"] == {"tool": {"name": "record_result"}}


def test_retries_once_with_error_feedback_then_succeeds():
    client = MagicMock()
    client.converse.side_effect = [_response({"value": "not-an-int"}), _response({"value": 3})]
    out = call_structured(client, "model-x", "prompt", Out)
    assert out.value == 3
    assert client.converse.call_count == 2
    retry_messages = client.converse.call_args.kwargs["messages"]
    assert len(retry_messages) == 3  # original + assistant + error feedback
    assert "failed validation" in retry_messages[-1]["content"][0]["text"]


def test_raises_after_second_validation_failure():
    client = MagicMock()
    client.converse.side_effect = [_response({"value": "a"}), _response({"value": "b"})]
    with pytest.raises(ValidationError):
        call_structured(client, "model-x", "prompt", Out)
    assert client.converse.call_count == 2


def test_no_tool_call_raises():
    client = MagicMock()
    client.converse.return_value = {"output": {"message": {"content": [{"text": "chatter"}]}}}
    with pytest.raises(RuntimeError, match="no tool call"):
        call_structured(client, "model-x", "prompt", Out)
