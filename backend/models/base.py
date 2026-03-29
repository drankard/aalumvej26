from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class RpcRequest(BaseModel):
    action: str
    payload: dict[str, Any] = {}


class RpcResponse(BaseModel):
    success: bool
    data: Any = None
    error: str | None = None
