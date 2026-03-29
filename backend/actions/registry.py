from __future__ import annotations

from typing import Any, Callable

_actions: dict[str, Callable[..., Any]] = {}


def register(name: str) -> Callable:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        _actions[name] = fn
        return fn
    return decorator


def dispatch(action: str, payload: dict[str, Any], **deps: Any) -> Any:
    if action not in _actions:
        raise ValueError(f"Unknown action: {action}")
    return _actions[action](payload, **deps)
