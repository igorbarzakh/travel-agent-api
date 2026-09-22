from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.travel_assistant import TravelAssistantService
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.repositories.refresh_session import RefreshSessionRepository


@pytest.fixture
def llm_client() -> Iterator[MagicMock]:
    with patch("app.services.travel_assistant.AsyncOpenAI") as client_factory:
        client = client_factory.return_value
        client.responses.create = AsyncMock()
        client.close = AsyncMock()

        yield client


@pytest.fixture
def travel_service(llm_client: MagicMock) -> TravelAssistantService:
    return TravelAssistantService()


@pytest.fixture
def user_repository() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def auth_service(
    user_repository: AsyncMock,
    refresh_session_repository: AsyncMock,
) -> AuthService:
    return AuthService(
        user_repository,
        refresh_session_repository,
    )


@pytest.fixture
def refresh_session_repository() -> AsyncMock:
    return AsyncMock(spec=RefreshSessionRepository)
