"""Bedrock structured-output wrapper: one forced tool call, Pydantic-validated.

No agent loop. Every model interaction is: prompt in → schema-enforced JSON out.
On validation failure the call is retried once with the error appended.
"""
from __future__ import annotations

import json
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _tool_config(name: str, model_cls: type[BaseModel]) -> dict:
    return {
        "tools": [{
            "toolSpec": {
                "name": name,
                "description": f"Record the result as {model_cls.__name__}.",
                "inputSchema": {"json": model_cls.model_json_schema()},
            }
        }],
        "toolChoice": {"tool": {"name": name}},
    }


def _extract_tool_input(response: dict) -> dict:
    for block in response["output"]["message"]["content"]:
        if "toolUse" in block:
            return block["toolUse"]["input"]
    raise RuntimeError("model returned no tool call")


def call_structured(
    client,
    model_id: str,
    prompt: str,
    result_model: type[T],
    tool_name: str = "record_result",
    max_tokens: int = 8192,
) -> T:
    """One Converse call with forced tool use; validates against result_model.

    Retries exactly once on schema/validation failure, appending the error.
    Raises on second failure — the pipeline reports the stage as failed rather
    than publishing unvalidated content.
    """
    tool_config = _tool_config(tool_name, result_model)
    messages = [{"role": "user", "content": [{"text": prompt}]}]

    for attempt in (1, 2):
        response = client.converse(
            modelId=model_id,
            messages=messages,
            toolConfig=tool_config,
            inferenceConfig={"maxTokens": max_tokens},
        )
        raw = _extract_tool_input(response)
        try:
            return result_model.model_validate(raw)
        except ValidationError as e:
            if attempt == 2:
                raise
            logger.warning(f"Validation failed (attempt 1), retrying: {e}")
            messages = messages + [
                response["output"]["message"],
                {"role": "user", "content": [{"text": (
                    "Your previous tool input failed validation:\n"
                    f"{e}\n\nCall the tool again with corrected input. "
                    f"Previous input was:\n{json.dumps(raw, ensure_ascii=False)[:4000]}"
                )}]},
            ]
    raise AssertionError("unreachable")
