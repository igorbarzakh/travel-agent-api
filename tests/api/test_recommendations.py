from unittest.mock import AsyncMock

from starlette.testclient import TestClient

from app.core.error_codes import ErrorCode
from app.core.exceptions import EmptyLLMResponseError, LLMRequestError
from app.core.messages import (
    EMPTY_LLM_RESPONSE_ERROR_MESSAGE,
    LLM_REQUEST_ERROR_MESSAGE,
)
from app.schemas.error import ErrorDetail


def test_get_recommendation_returns_success(
    client: TestClient, travel_service_mock: AsyncMock
) -> None:
    # Arrange
    query = "Что посмотреть в Гонконге?"
    answer = "Посетите Victoria Peak."
    travel_service_mock.get_recommendation.return_value = answer

    # Act
    response = client.post(
        "/recommendations",
        json={"query": query},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "answer": answer,
    }
    travel_service_mock.get_recommendation.assert_awaited_once_with(query)


def test_get_recommendation_rejects_empty_query(
    client: TestClient, travel_service_mock: AsyncMock
) -> None:
    # Act
    response = client.post(
        "/recommendations",
        json={"query": ""},
    )

    # Assert
    assert response.status_code == 422
    travel_service_mock.get_recommendation.assert_not_awaited()


def test_get_recommendation_returns_502_on_llm_error(
    client: TestClient,
    travel_service_mock: AsyncMock,
) -> None:
    # Arrange
    travel_service_mock.get_recommendation.side_effect = LLMRequestError()

    # Act
    response = client.post(
        "/recommendations",
        json={"query": "Что посмотреть в Гонконге?"},
    )

    # Assert
    assert response.status_code == 502
    assert response.json() == {
        "detail": {
            "code": ErrorCode.LLM_REQUEST_FAILED,
            "message": LLM_REQUEST_ERROR_MESSAGE,
        }
    }


def test_get_recommendation_returns_502_on_empty_llm_response(
    client: TestClient,
    travel_service_mock: AsyncMock,
) -> None:
    # Arrange
    travel_service_mock.get_recommendation.side_effect = EmptyLLMResponseError()

    # Act
    response = client.post(
        "/recommendations",
        json={"query": "Что посмотреть в Гонконге?"},
    )

    # Assert
    assert response.status_code == 502
    assert response.json() == {
        "detail": {
            "code": ErrorCode.EMPTY_LLM_RESPONSE,
            "message": EMPTY_LLM_RESPONSE_ERROR_MESSAGE,
        }
    }


def test_stream_recommendation_returns_sse_events(
    client: TestClient,
    travel_service_mock: AsyncMock,
) -> None:
    # Arrange
    async def fake_stream():
        yield "Посетите"
        yield " Victoria Peak"

    travel_service_mock.get_stream_recommendation.return_value = fake_stream()

    # Act
    response = client.post(
        "/recommendations/stream",
        json={"query": "Что посмотреть в Гонконге?"},
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == (
        "event: message\n"
        'data: {"text":"Посетите"}\n\n'
        "event: message\n"
        'data: {"text":" Victoria Peak"}\n\n'
        "event: done\n"
        "data: {}\n\n"
    )


def test_stream_recommendation_returns_error_event(
    client: TestClient,
    travel_service_mock: AsyncMock,
) -> None:
    # Arrange
    async def fake_stream():
        if False:
            yield ""

        raise LLMRequestError()

    travel_service_mock.get_stream_recommendation.return_value = fake_stream()

    error_data = ErrorDetail(
        code=ErrorCode.LLM_REQUEST_FAILED,
        message=LLM_REQUEST_ERROR_MESSAGE,
    )

    # Act
    response = client.post(
        "/recommendations/stream",
        json={"query": "Что посмотреть в Гонконге?"},
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == f"event: error\ndata: {error_data.model_dump_json()}\n\n"


def test_stream_recommendation_rejects_empty_query(
    client: TestClient, travel_service_mock: AsyncMock
) -> None:
    # Act
    response = client.post(
        "/recommendations/stream",
        json={"query": ""},
    )

    # Assert
    assert response.status_code == 422
    travel_service_mock.get_stream_recommendation.assert_not_called()


def test_stream_recommendation_rejects_invalid_json(
    client: TestClient, travel_service_mock: AsyncMock
) -> None:
    # Act
    response = client.post(
        "/recommendations/stream",
        content='{"query": "Гонконг",}',
        headers={"Content-Type": "application/json"},
    )

    # Assert
    assert response.status_code == 422
    travel_service_mock.get_stream_recommendation.assert_not_called()


def test_stream_recommendation_returns_empty_response_error_event(
    client: TestClient,
    travel_service_mock: AsyncMock,
) -> None:
    # Arrange
    async def fake_stream():
        if False:
            yield ""

        raise EmptyLLMResponseError()

    travel_service_mock.get_stream_recommendation.return_value = fake_stream()

    error_data = ErrorDetail(
        code=ErrorCode.EMPTY_LLM_RESPONSE,
        message=EMPTY_LLM_RESPONSE_ERROR_MESSAGE,
    )

    # Act
    response = client.post(
        "/recommendations/stream",
        json={"query": "Что посмотреть в Гонконге?"},
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == f"event: error\ndata: {error_data.model_dump_json()}\n\n"
