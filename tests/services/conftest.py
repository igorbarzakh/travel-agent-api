from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.travel_assistant import TravelAssistantService


@pytest.fixture
def llm_client() -> Iterator[MagicMock]:
    with patch(
        "app.services.travel_assistant.AsyncOpenAI"
    ) as client_factory:
        client = client_factory.return_value
        client.chat.completions.create = AsyncMock()
        client.close = AsyncMock()

        yield client


@pytest.fixture
def travel_service(llm_client: MagicMock) -> TravelAssistantService:
    return TravelAssistantService()