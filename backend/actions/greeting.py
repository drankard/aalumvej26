from __future__ import annotations

from typing import Any

from actions.registry import register
from models.greeting import Greeting, GreetingCreate
from repositories.greeting import GreetingRepository


@register("hello")
def hello_action(payload: dict[str, Any], *, greeting_repo: GreetingRepository, **_: Any) -> dict[str, Any]:
    data = GreetingCreate(**payload)
    greeting = greeting_repo.create(data)
    return greeting.model_dump()


@register("list_greetings")
def list_greetings_action(payload: dict[str, Any], *, greeting_repo: GreetingRepository, **_: Any) -> list[dict[str, Any]]:
    greetings = greeting_repo.list_all()
    return [g.model_dump() for g in greetings]
