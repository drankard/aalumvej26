from __future__ import annotations

from unittest.mock import patch

from models.greeting import GreetingCreate


def test_create_greeting(mock_db, greeting_repo):
    data = GreetingCreate(name="World")

    with patch("repositories.greeting.uuid") as mock_uuid, \
         patch("repositories.greeting.datetime") as mock_dt:
        mock_uuid.uuid4.return_value = "test-uuid-1234"
        mock_dt.now.return_value.isoformat.return_value = "2026-01-01T00:00:00+00:00"
        mock_dt.timezone = __import__("datetime").timezone

        result = greeting_repo.create(data)

    assert result.id == "test-uuid-1234"
    assert result.name == "World"
    assert result.message == "Hello, World!"
    assert result.created_at == "2026-01-01T00:00:00+00:00"
    mock_db.put_item.assert_called_once()

    call_args = mock_db.put_item.call_args[0][0]
    assert call_args["pk"] == "GREETING"
    assert call_args["sk"] == "GREETING#test-uuid-1234"


def test_list_greetings_returns_models(mock_db, greeting_repo):
    mock_db.query.return_value = [
        {"id": "1", "name": "Alice", "message": "Hello, Alice!", "created_at": "2026-01-01"},
        {"id": "2", "name": "Bob", "message": "Hello, Bob!", "created_at": "2026-01-02"},
    ]

    result = greeting_repo.list_all()

    assert len(result) == 2
    assert result[0].name == "Alice"
    assert result[0].message == "Hello, Alice!"
    assert result[1].name == "Bob"
    mock_db.query.assert_called_once_with("GREETING", ScanIndexForward=False)


def test_list_greetings_empty(mock_db, greeting_repo):
    mock_db.query.return_value = []

    result = greeting_repo.list_all()

    assert result == []
