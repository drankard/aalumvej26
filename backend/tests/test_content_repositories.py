from __future__ import annotations

from unittest.mock import patch

from models.content import PostCreate, PostTranslation, AreaCreate, AreaTranslation, PostUpdate


def test_create_post(mock_db, post_repo):
    data = PostCreate(
        category="surf",
        tag_key="event",
        url="https://example.com",
        emoji="🏄",
        sort_order=1,
        translations={
            "da": PostTranslation(title="Dansk titel", excerpt="Dansk tekst", date="1. jan"),
            "en": PostTranslation(title="English title", excerpt="English text", date="Jan 1"),
        },
    )

    with patch("repositories.content.uuid") as mock_uuid, \
         patch("repositories.content.datetime") as mock_dt:
        mock_uuid.uuid4.return_value = "test-post-id"
        mock_dt.now.return_value.isoformat.return_value = "2026-01-01T00:00:00+00:00"
        mock_dt.timezone = __import__("datetime").timezone

        result = post_repo.create(data)

    assert result.id == "test-post-id"
    assert result.category == "surf"
    assert result.tag_key == "event"
    assert result.translations["da"].title == "Dansk titel"
    assert result.translations["en"].excerpt == "English text"
    mock_db.put_item.assert_called_once()

    call_args = mock_db.put_item.call_args[0][0]
    assert call_args["pk"] == "POST"
    assert call_args["sk"] == "POST#test-post-id"


def test_list_published_posts(mock_db, post_repo):
    mock_db.query.return_value = [
        {
            "id": "1", "category": "natur", "tag_key": "guide", "url": "https://a.com",
            "emoji": "🥾", "sort_order": 2, "status": "published", "relevance_score": 20,
            "source_urls": [], "translations": {"da": {"title": "A", "excerpt": "A", "date": "A"}},
            "created_at": "2026-01-01", "updated_at": "2026-01-01",
        },
        {
            "id": "2", "category": "surf", "tag_key": "event", "url": "https://b.com",
            "emoji": "🏄", "sort_order": 1, "status": "published", "relevance_score": 15,
            "source_urls": [], "translations": {"da": {"title": "B", "excerpt": "B", "date": "B"}},
            "created_at": "2026-01-02", "updated_at": "2026-01-02",
        },
        {
            "id": "3", "category": "mad", "tag_key": "guide", "url": "https://c.com",
            "emoji": "🦪", "sort_order": 3, "status": "archived", "relevance_score": 10,
            "source_urls": [], "translations": {"da": {"title": "C", "excerpt": "C", "date": "C"}},
            "created_at": "2026-01-03", "updated_at": "2026-01-03",
        },
    ]

    result = post_repo.list_published()

    assert len(result) == 2
    assert result[0].sort_order == 1
    assert result[1].sort_order == 2


def test_list_archived_posts(mock_db, post_repo):
    mock_db.query.return_value = [
        {
            "id": "1", "category": "natur", "tag_key": "guide", "url": "https://a.com",
            "emoji": "🥾", "sort_order": 1, "status": "published",
            "translations": {"da": {"title": "A", "excerpt": "A", "date": "A"}},
            "created_at": "2026-01-01", "updated_at": "2026-01-01",
        },
        {
            "id": "2", "category": "mad", "tag_key": "guide", "url": "https://b.com",
            "emoji": "🦪", "sort_order": 2, "status": "archived",
            "translations": {"da": {"title": "B", "excerpt": "B", "date": "B"}},
            "created_at": "2026-01-02", "updated_at": "2026-01-02",
        },
    ]

    result = post_repo.list_archived()

    assert len(result) == 1
    assert result[0].id == "2"


def test_get_post(mock_db, post_repo):
    mock_db.get_item.return_value = {
        "id": "abc", "category": "natur", "tag_key": "guide", "url": "https://a.com",
        "emoji": "🥾", "sort_order": 1, "status": "published",
        "translations": {"da": {"title": "T", "excerpt": "E", "date": "D"}},
        "created_at": "2026-01-01", "updated_at": "2026-01-01",
    }

    result = post_repo.get("abc")

    assert result is not None
    assert result.id == "abc"
    mock_db.get_item.assert_called_once_with({"pk": "POST", "sk": "POST#abc"})


def test_get_post_not_found(mock_db, post_repo):
    mock_db.get_item.return_value = None

    result = post_repo.get("missing")

    assert result is None


def test_update_post(mock_db, post_repo):
    mock_db.get_item.return_value = {
        "pk": "POST", "sk": "POST#abc",
        "id": "abc", "category": "natur", "tag_key": "guide", "url": "https://a.com",
        "emoji": "🥾", "sort_order": 1, "status": "published",
        "translations": {"da": {"title": "Old", "excerpt": "E", "date": "D"}},
        "created_at": "2026-01-01", "updated_at": "2026-01-01",
    }

    with patch("repositories.content.datetime") as mock_dt:
        mock_dt.now.return_value.isoformat.return_value = "2026-02-01T00:00:00+00:00"
        mock_dt.timezone = __import__("datetime").timezone

        result = post_repo.update("abc", PostUpdate(category="surf"))

    assert result is not None
    assert result.category == "surf"
    assert result.tag_key == "guide"
    mock_db.put_item.assert_called_once()


def test_delete_post(mock_db, post_repo):
    post_repo.delete("abc")

    mock_db.delete_item.assert_called_once_with({"pk": "POST", "sk": "POST#abc"})


def test_create_area(mock_db, area_repo):
    data = AreaCreate(
        url="https://example.com",
        sort_order=0,
        translations={
            "da": AreaTranslation(name="Thy", dist="Omgiver Agger", desc="Nationalpark"),
        },
    )

    with patch("repositories.content.uuid") as mock_uuid, \
         patch("repositories.content.datetime") as mock_dt:
        mock_uuid.uuid4.return_value = "test-area-id"
        mock_dt.now.return_value.isoformat.return_value = "2026-01-01T00:00:00+00:00"
        mock_dt.timezone = __import__("datetime").timezone

        result = area_repo.create(data)

    assert result.id == "test-area-id"
    assert result.translations["da"].name == "Thy"
    mock_db.put_item.assert_called_once()

    call_args = mock_db.put_item.call_args[0][0]
    assert call_args["pk"] == "AREA"
    assert call_args["sk"] == "AREA#test-area-id"


def test_list_published_areas(mock_db, area_repo):
    mock_db.query.return_value = [
        {
            "id": "1", "url": "https://a.com", "sort_order": 1, "status": "published",
            "translations": {"da": {"name": "A", "dist": "1km", "desc": "A"}},
            "created_at": "2026-01-01", "updated_at": "2026-01-01",
        },
        {
            "id": "2", "url": "https://b.com", "sort_order": 0, "status": "published",
            "translations": {"da": {"name": "B", "dist": "2km", "desc": "B"}},
            "created_at": "2026-01-02", "updated_at": "2026-01-02",
        },
    ]

    result = area_repo.list_published()

    assert len(result) == 2
    assert result[0].sort_order == 0
    assert result[1].sort_order == 1
