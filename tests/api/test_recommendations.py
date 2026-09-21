from unittest.mock import AsyncMock

from starlette.testclient import TestClient

from app.core.exceptions import LLMRequestError, EmptyLLMResponseError
from app.core.messages import LLM_REQUEST_ERROR_MESSAGE, EMPTY_LLM_RESPONSE_ERROR_MESSAGE


def test_get_recommendations_success(client: TestClient, travel_service_mock: AsyncMock) -> None:
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

def test_create_recommendation_rejects_empty_query(
    client: TestClient,
    travel_service_mock: AsyncMock,
) -> None:
    # Act
    response = client.post(
        "/recommendations",
        json={"query": ""},
    )

    # Assert
    assert response.status_code == 422
    travel_service_mock.get_recommendation.assert_not_awaited()

def test_create_recommendation_returns_502_on_llm_error(
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
        "detail": LLM_REQUEST_ERROR_MESSAGE,
    }

def test_create_recommendation_returns_502_on_empty_llm_response(
    client: TestClient,
    travel_service_mock: AsyncMock,
) -> None:
    # Arrange
    travel_service_mock.get_recommendation.side_effect = (
        EmptyLLMResponseError()
    )

    # Act
    response = client.post(
        "/recommendations",
        json={"query": "Что посмотреть в Гонконге?"},
    )

    # Assert
    assert response.status_code == 502
    assert response.json() == {
        "detail": EMPTY_LLM_RESPONSE_ERROR_MESSAGE,
    }


def test_stream_recommendation_returns_streamed_text(
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
    assert response.text == "Посетите Victoria Peak"

def test_stream_recommendation_rejects_empty_query(
    client: TestClient,
    travel_service_mock: AsyncMock,
) -> None:
    # Act
    response = client.post(
        "/recommendations/stream",
        json={"query": ""},
    )

    # Assert
    assert response.status_code == 422
    travel_service_mock.get_stream_recommendation.assert_not_called()
