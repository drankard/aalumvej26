from __future__ import annotations

from unittest.mock import MagicMock

from actions.greeting import hello_action, list_greetings_action
from models.greeting import Greeting


def test_hello_action_creates_greeting():
    mock_repo = MagicMock()
    mock_repo.create.return_value = Greeting(
        id="abc-123",
        name="World",
        message="Hello, World!",
        created_at="2026-01-01T00:00:00+00:00",
    )

    result = hello_action({"name": "World"}, greeting_repo=mock_repo)

    assert result["name"] == "World"
    assert result["message"] == "Hello, World!"
    assert result["id"] == "abc-123"
    mock_repo.create.assert_called_once()


def test_hello_action_validates_payload():
    mock_repo = MagicMock()

    try:
        hello_action({}, greeting_repo=mock_repo)
        assert False, "Should have raised ValidationError"
    except Exception:
        pass

    mock_repo.create.assert_not_called()


def test_list_greetings_action_returns_list():
    mock_repo = MagicMock()
    mock_repo.list_all.return_value = [
        Greeting(id="1", name="Alice", message="Hello, Alice!", created_at="2026-01-01"),
    ]

    result = list_greetings_action({}, greeting_repo=mock_repo)

    assert len(result) == 1
    assert result[0]["name"] == "Alice"


def test_list_greetings_action_empty():
    mock_repo = MagicMock()
    mock_repo.list_all.return_value = []

    result = list_greetings_action({}, greeting_repo=mock_repo)

    assert result == []
