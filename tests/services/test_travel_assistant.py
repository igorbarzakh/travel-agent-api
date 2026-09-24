import pytest
import asyncio
from httpx import Request

from types import SimpleNamespace
from unittest.mock import MagicMock

from openai import APIError
from openai.types.responses import ResponseTextDeltaEvent


from app.services.travel_assistant import TravelAssistantService
from app.core.exceptions import EmptyLLMResponseError, LLMRequestError
from app.schemas.chat import ChatMessage
from app.core.prompts import TRAVEL_SYSTEM_PROMPT


def test_get_recommendation_returns_trimmed_text(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    llm_client.responses.create.return_value = SimpleNamespace(
        output_text="  Посетите набережную.  ",
    )

    # Act
    answer = asyncio.run(
        travel_service.get_recommendation("Что посмотреть в Гонконге?", [])
    )

    # Assert
    assert answer == "Посетите набережную."
    llm_client.responses.create.assert_awaited_once()


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
    llm_client.responses.create.return_value = SimpleNamespace(
        output_text=content,
    )

    # Act & Assert
    with pytest.raises(EmptyLLMResponseError):
        asyncio.run(
            travel_service.get_recommendation(
                "Что посмотреть в Гонконге?",
                [],
            )
        )


def test_get_recommendation_wraps_api_error(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    api_error = APIError(
        message="Service unavailable",
        request=Request(
            "POST",
            "https://api.groq.com/openai/v1/responses",
        ),
        body=None,
    )
    llm_client.responses.create.side_effect = api_error

    # Act & Assert
    with pytest.raises(LLMRequestError) as exc_info:
        asyncio.run(
            travel_service.get_recommendation(
                "Что посмотреть в Гонконге?",
                [],
            )
        )

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
        yield ResponseTextDeltaEvent(
            content_index=0,
            delta="Посетите",
            item_id="item_1",
            logprobs=[],
            output_index=0,
            sequence_number=1,
            type="response.output_text.delta",
        )
        yield ResponseTextDeltaEvent(
            content_index=0,
            delta=" Victoria Peak",
            item_id="item_1",
            logprobs=[],
            output_index=0,
            sequence_number=2,
            type="response.output_text.delta",
        )

    llm_client.responses.create.return_value = fake_stream()

    async def collect_chunks() -> list[str]:
        chunks = []

        async for chunk in travel_service.get_stream_recommendation(
            "Что посмотреть в Гонконге?",
            [],
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
    llm_client.responses.create.assert_awaited_once()


def test_stream_recommendation_skips_empty_chunks(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    async def fake_stream():
        yield SimpleNamespace(type="response.created")
        yield ResponseTextDeltaEvent(
            content_index=0,
            delta="",
            item_id="item_1",
            logprobs=[],
            output_index=0,
            sequence_number=1,
            type="response.output_text.delta",
        )
        yield ResponseTextDeltaEvent(
            content_index=0,
            delta="Victoria Peak",
            item_id="item_1",
            logprobs=[],
            output_index=0,
            sequence_number=2,
            type="response.output_text.delta",
        )

    llm_client.responses.create.return_value = fake_stream()

    async def collect_chunks() -> list[str]:
        chunks = []

        async for chunk in travel_service.get_stream_recommendation(
            "Что посмотреть в Гонконге?", []
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
            "https://api.groq.com/openai/v1/responses",
        ),
        body=None,
    )
    llm_client.responses.create.side_effect = api_error

    async def consume_stream() -> None:
        async for _ in travel_service.get_stream_recommendation(
            "Что посмотреть в Гонконге?", []
        ):
            pass

    # Act & Assert
    with pytest.raises(LLMRequestError) as exc_info:
        asyncio.run(consume_stream())

    assert exc_info.value.__cause__ is api_error


@pytest.mark.parametrize("emit_chunk", [False, True], ids=["before-text", "after-text"])
def test_stream_recommendation_wraps_api_error_during_iteration(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
    emit_chunk: bool,
) -> None:
    # Arrange
    api_error = APIError(
        message="Stream interrupted",
        request=Request("POST", "https://api.groq.com/openai/v1/responses"),
        body=None,
    )

    async def fake_stream():
        if emit_chunk:
            yield ResponseTextDeltaEvent(
                content_index=0,
                delta="Посетите",
                item_id="item_1",
                logprobs=[],
                output_index=0,
                sequence_number=1,
                type="response.output_text.delta",
            )
        raise api_error

    llm_client.responses.create.return_value = fake_stream()
    chunks = []

    async def consume_stream() -> None:
        async for chunk in travel_service.get_stream_recommendation(
            "Что посмотреть в Гонконге?", []
        ):
            chunks.append(chunk)

    # Act & Assert
    with pytest.raises(LLMRequestError) as exc_info:
        asyncio.run(consume_stream())

    assert exc_info.value.__cause__ is api_error
    assert chunks == (["Посетите"] if emit_chunk else [])


def test_stream_recommendation_rejects_empty_stream(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    async def fake_stream():
        if False:
            yield

    llm_client.responses.create.return_value = fake_stream()

    async def consume_stream() -> None:
        async for _ in travel_service.get_stream_recommendation(
            "Что посмотреть в Гонконге?", []
        ):
            pass

    # Act & Assert
    with pytest.raises(EmptyLLMResponseError):
        asyncio.run(consume_stream())


def test_get_recommendation_sends_history(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    history = [
        ChatMessage(
            role="user",
            content="Что посмотреть в Гонконге?",
        ),
        ChatMessage(
            role="assistant",
            content="Посетите Victoria Peak.",
        ),
    ]

    llm_client.responses.create.return_value = SimpleNamespace(
        output_text="Он находится на острове Гонконг.",
    )

    # Act
    asyncio.run(
        travel_service.get_recommendation(
            "А где это находится?",
            history,
        )
    )

    # Assert
    llm_client.responses.create.assert_awaited_once_with(
        model=travel_service._model,
        instructions=TRAVEL_SYSTEM_PROMPT,
        input=[
            {
                "role": "user",
                "content": "Что посмотреть в Гонконге?",
            },
            {
                "role": "assistant",
                "content": "Посетите Victoria Peak.",
            },
            {
                "role": "user",
                "content": "А где это находится?",
            },
        ],
    )


def test_stream_recommendation_sends_history(
    travel_service: TravelAssistantService,
    llm_client: MagicMock,
) -> None:
    # Arrange
    history = [
        ChatMessage(
            role="user",
            content="Что посмотреть в Гонконге?",
        ),
        ChatMessage(
            role="assistant",
            content="Посетите Victoria Peak.",
        ),
    ]

    async def fake_stream():
        yield ResponseTextDeltaEvent(
            content_index=0,
            delta="Он находится на острове Гонконг.",
            item_id="item_1",
            logprobs=[],
            output_index=0,
            sequence_number=1,
            type="response.output_text.delta",
        )

    llm_client.responses.create.return_value = fake_stream()

    async def consume_stream() -> None:
        async for _ in travel_service.get_stream_recommendation(
            "А где это находится?",
            history,
        ):
            pass

    # Act
    asyncio.run(consume_stream())

    # Assert
    llm_client.responses.create.assert_awaited_once_with(
        model=travel_service._model,
        instructions=TRAVEL_SYSTEM_PROMPT,
        input=[
            {
                "role": "user",
                "content": "Что посмотреть в Гонконге?",
            },
            {
                "role": "assistant",
                "content": "Посетите Victoria Peak.",
            },
            {
                "role": "user",
                "content": "А где это находится?",
            },
        ],
        stream=True,
    )
