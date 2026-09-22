from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_auth_service,
    get_travel_service,
)
from app.main import app
from app.services.travel_assistant import TravelAssistantService
from app.services.auth import AuthService


@pytest.fixture
def travel_service_mock() -> AsyncMock:
    return AsyncMock(spec=TravelAssistantService)


@pytest.fixture
def auth_service_mock() -> AsyncMock:
    return AsyncMock(spec=AuthService)


@pytest.fixture
def client(
    travel_service_mock: AsyncMock, auth_service_mock: AsyncMock
) -> Iterator[TestClient]:
    app.dependency_overrides[get_travel_service] = lambda: travel_service_mock
    app.dependency_overrides[get_auth_service] = lambda: auth_service_mock

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
