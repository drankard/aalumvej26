from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from repositories.base import DynamoDBAdapter
from repositories.greeting import GreetingRepository
from repositories.content import PostRepository, AreaRepository


@pytest.fixture
def mock_db() -> MagicMock:
    return MagicMock(spec=DynamoDBAdapter)


@pytest.fixture
def greeting_repo(mock_db: MagicMock) -> GreetingRepository:
    return GreetingRepository(mock_db)


@pytest.fixture
def post_repo(mock_db: MagicMock) -> PostRepository:
    return PostRepository(mock_db)


@pytest.fixture
def area_repo(mock_db: MagicMock) -> AreaRepository:
    return AreaRepository(mock_db)
