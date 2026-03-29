from __future__ import annotations

from pydantic import BaseModel


class GreetingCreate(BaseModel):
    name: str


class Greeting(BaseModel):
    id: str
    name: str
    message: str
    created_at: str
