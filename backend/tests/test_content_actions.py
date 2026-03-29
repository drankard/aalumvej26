from __future__ import annotations

from unittest.mock import MagicMock

from actions.content import (
    list_posts_action, list_areas_action, list_content_action,
    list_archived_posts_action, create_post_action, update_post_action,
    delete_post_action, archive_post_action, create_area_action,
)
from models.content import (
    Post, PostTranslation, Area, AreaTranslation,
)


def _make_post(id: str = "p1", category: str = "surf", status: str = "published") -> Post:
    return Post(
        id=id, category=category, tag_key="event", url="https://example.com",
        emoji="🏄", sort_order=1, status=status, relevance_score=20,
        source_urls=[], translations={
            "da": PostTranslation(title="Titel", excerpt="Tekst", date="1. jan"),
        },
        created_at="2026-01-01", updated_at="2026-01-01",
    )


def _make_area(id: str = "a1") -> Area:
    return Area(
        id=id, url="https://example.com", sort_order=0, status="published",
        translations={
            "da": AreaTranslation(name="Thy", dist="0 km", desc="Nationalpark"),
        },
        created_at="2026-01-01", updated_at="2026-01-01",
    )


def test_list_posts_action():
    mock_repo = MagicMock()
    mock_repo.list_published.return_value = [_make_post()]

    result = list_posts_action({}, post_repo=mock_repo)

    assert len(result) == 1
    assert result[0]["category"] == "surf"


def test_list_areas_action():
    mock_repo = MagicMock()
    mock_repo.list_published.return_value = [_make_area()]

    result = list_areas_action({}, area_repo=mock_repo)

    assert len(result) == 1
    assert result[0]["translations"]["da"]["name"] == "Thy"


def test_list_content_action():
    mock_post_repo = MagicMock()
    mock_area_repo = MagicMock()
    mock_category_repo = MagicMock()
    mock_post_repo.list_published.return_value = [_make_post()]
    mock_area_repo.list_published.return_value = [_make_area()]
    mock_category_repo.list_all.return_value = []

    result = list_content_action({}, post_repo=mock_post_repo, area_repo=mock_area_repo, category_repo=mock_category_repo)

    assert len(result["posts"]) == 1
    assert len(result["areas"]) == 1
    assert len(result["categories"]) == 0


def test_list_archived_posts_action():
    mock_repo = MagicMock()
    mock_repo.list_archived.return_value = [_make_post(status="archived")]

    result = list_archived_posts_action({}, post_repo=mock_repo)

    assert len(result) == 1
    assert result[0]["status"] == "archived"


def test_create_post_action():
    mock_repo = MagicMock()
    mock_repo.create.return_value = _make_post()

    result = create_post_action({
        "category": "surf", "tag_key": "event", "url": "https://example.com",
        "emoji": "🏄", "translations": {
            "da": {"title": "T", "excerpt": "E", "date": "D"},
        },
    }, post_repo=mock_repo)

    assert result["id"] == "p1"
    mock_repo.create.assert_called_once()


def test_create_post_validates_payload():
    mock_repo = MagicMock()

    try:
        create_post_action({}, post_repo=mock_repo)
        assert False, "Should have raised"
    except Exception:
        pass

    mock_repo.create.assert_not_called()


def test_update_post_action():
    mock_repo = MagicMock()
    mock_repo.update.return_value = _make_post()

    result = update_post_action({"id": "p1", "category": "natur"}, post_repo=mock_repo)

    assert result["id"] == "p1"
    mock_repo.update.assert_called_once()


def test_update_post_not_found():
    mock_repo = MagicMock()
    mock_repo.update.return_value = None

    try:
        update_post_action({"id": "missing", "category": "natur"}, post_repo=mock_repo)
        assert False, "Should have raised"
    except ValueError as e:
        assert "not found" in str(e)


def test_delete_post_action():
    mock_repo = MagicMock()

    result = delete_post_action({"id": "p1"}, post_repo=mock_repo)

    assert result["deleted"] is True
    mock_repo.delete.assert_called_once_with("p1")


def test_archive_post_action():
    mock_repo = MagicMock()
    mock_repo.update.return_value = _make_post(status="archived")

    result = archive_post_action({"id": "p1"}, post_repo=mock_repo)

    assert result["status"] == "archived"
    mock_repo.update.assert_called_once()


def test_create_area_action():
    mock_repo = MagicMock()
    mock_repo.create.return_value = _make_area()

    result = create_area_action({
        "url": "https://example.com",
        "translations": {"da": {"name": "Thy", "dist": "0 km", "desc": "Park"}},
    }, area_repo=mock_repo)

    assert result["id"] == "a1"
    mock_repo.create.assert_called_once()
