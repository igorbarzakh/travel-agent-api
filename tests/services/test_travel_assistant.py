import pytest
import asyncio
from httpx import Request
from openai import APIError


from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.travel_assistant import TravelAssistantService
from app.core.exceptions import EmptyLLMResponseError, LLMRequestError


def test_get_recommendation_returns_trimmed_text(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    llm_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="  Посетите набережную.  ",
                ),
            ),
        ],
    )

    # Act
    answer = asyncio.run(
        travel_service.get_recommendation("Что посмотреть в Гонконге?")
    )

    # Assert
    assert answer == "Посетите набережную."
    llm_client.chat.completions.create.assert_awaited_once()


@pytest.mark.parametrize(
    "content",
    [None, "", "   \n\t"],
    ids=["none", "empty-string", "whitespace"],
)
def test_get_recommendation_rejects_empty_content(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
    content: str | None,
) -> None:
    # Arrange
    llm_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            ),
        ],
    )

    # Act & Assert
    with pytest.raises(EmptyLLMResponseError):
        asyncio.run(travel_service.get_recommendation("Что посмотреть в Гонконге?"))


def test_get_recommendation_rejects_empty_choices(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    llm_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[],
    )

    # Act & Assert
    with pytest.raises(EmptyLLMResponseError):
        asyncio.run(travel_service.get_recommendation("Что посмотреть в Гонконге?"))


def test_get_recommendation_wraps_api_error(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    api_error = APIError(
        message="Service unavailable",
        request=Request(
            "POST",
            "https://api.groq.com/openai/v1/chat/completions",
        ),
        body=None,
    )
    llm_client.chat.completions.create.side_effect = api_error

    # Act & Assert
    with pytest.raises(LLMRequestError) as exc_info:
        asyncio.run(travel_service.get_recommendation("Что посмотреть в Гонконге?"))

    assert exc_info.value.__cause__ is api_error


def test_close_llm_client(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    llm_client.close.return_value = None

    # Act
    asyncio.run(travel_service.close())

    # Assert
    llm_client.close.assert_awaited_once_with()


def test_stream_recommendation_returns_chunks(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    async def fake_stream():
        yield SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content="Посетите"))]
        )
        yield SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=" Victoria Peak"))]
        )

    llm_client.chat.completions.create.return_value = fake_stream()

    async def collect_chunks() -> list[str]:
        chunks = []

        async for chunk in travel_service.get_stream_recommendation(
            "Что посмотреть в Гонконге?"
        ):
            chunks.append(chunk)

        return chunks

    # Act
    chunks = asyncio.run(collect_chunks())

    # Assert
    assert chunks == [
        "Посетите",
        " Victoria Peak",
    ]
    llm_client.chat.completions.create.assert_awaited_once()


def test_stream_recommendation_skips_empty_chunks(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    async def fake_stream():
        yield SimpleNamespace(choices=[])
        yield SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=None))]
        )
        yield SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=""))]
        )
        yield SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content="Victoria Peak"))]
        )

    llm_client.chat.completions.create.return_value = fake_stream()

    async def collect_chunks() -> list[str]:
        chunks = []

        async for chunk in travel_service.get_stream_recommendation(
            "Что посмотреть в Гонконге?"
        ):
            chunks.append(chunk)

        return chunks

    # Act
    chunks = asyncio.run(collect_chunks())

    # Assert
    assert chunks == ["Victoria Peak"]


def test_stream_recommendation_wraps_api_error(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    api_error = APIError(
        message="Service unavailable",
        request=Request(
            "POST",
            "https://api.groq.com/openai/v1/chat/completions",
        ),
        body=None,
    )
    llm_client.chat.completions.create.side_effect = api_error

    async def consume_stream() -> None:
        async for _ in travel_service.get_stream_recommendation(
            "Что посмотреть в Гонконге?"
        ):
            pass

    # Act & Assert
    with pytest.raises(LLMRequestError) as exc_info:
        asyncio.run(consume_stream())

    assert exc_info.value.__cause__ is api_error
