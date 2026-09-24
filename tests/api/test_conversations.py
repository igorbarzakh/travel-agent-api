from datetime import UTC, datetime
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.core.error_codes import ErrorCode
from app.core.exceptions import (
    ConversationNotFoundError,
    EmptyLLMResponseError,
    LLMRequestError,
)
from app.core.messages import (
    CONVERSATION_NOT_FOUND_ERROR_MESSAGE,
    EMPTY_LLM_RESPONSE_ERROR_MESSAGE,
    LLM_REQUEST_ERROR_MESSAGE,
)
from app.db.models.user import User
from app.schemas.conversation import (
    MessagePageResponse,
    MessageResponse,
)


def test_send_message_returns_assistant_message(
    client: TestClient,
    current_user: User,
    conversation_service_mock: AsyncMock,
) -> None:
    # Arrange
    conversation_service_mock.send_message.return_value = MessageResponse(
        id=2,
        conversation_id=1,
        role="assistant",
        content="Можно рассмотреть Японию.",
        created_at=datetime.now(UTC),
    )

    # Act
    response = client.post(
        "/conversations/1/messages",
        json={
            "content": "Куда поехать в ноябре?",
        },
    )

    # Assert
    assert response.status_code == 201

    conversation_service_mock.send_message.assert_awaited_once_with(
        conversation_id=1,
        user_id=current_user.id,
        content="Куда поехать в ноябре?",
    )

    response_data = response.json()

    assert response_data["id"] == 2
    assert response_data["conversation_id"] == 1
    assert response_data["role"] == "assistant"
    assert response_data["content"] == "Можно рассмотреть Японию."


def test_send_message_returns_502_on_llm_error(
    client: TestClient,
    conversation_service_mock: AsyncMock,
) -> None:
    # Arrange
    conversation_service_mock.send_message.side_effect = LLMRequestError()

    # Act
    response = client.post(
        "/conversations/1/messages",
        json={"content": "Куда поехать?"},
    )

    # Assert
    assert response.status_code == 502
    assert response.json() == {
        "detail": {
            "code": ErrorCode.LLM_REQUEST_FAILED,
            "message": LLM_REQUEST_ERROR_MESSAGE,
        }
    }


def test_send_message_returns_502_on_empty_llm_response(
    client: TestClient,
    conversation_service_mock: AsyncMock,
) -> None:
    # Arrange
    conversation_service_mock.send_message.side_effect = EmptyLLMResponseError()

    # Act
    response = client.post(
        "/conversations/1/messages",
        json={"content": "Куда поехать?"},
    )

    # Assert
    assert response.status_code == 502
    assert response.json() == {
        "detail": {
            "code": ErrorCode.EMPTY_LLM_RESPONSE,
            "message": EMPTY_LLM_RESPONSE_ERROR_MESSAGE,
        }
    }


def test_send_message_returns_404_for_unknown_conversation(
    client: TestClient,
    conversation_service_mock: AsyncMock,
) -> None:
    # Arrange
    conversation_service_mock.send_message.side_effect = ConversationNotFoundError()

    # Act
    response = client.post(
        "/conversations/999/messages",
        json={
            "content": "Куда поехать?",
        },
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": ErrorCode.CONVERSATION_NOT_FOUND,
            "message": CONVERSATION_NOT_FOUND_ERROR_MESSAGE,
        }
    }

    def test_get_messages_returns_paginated_messages(
        client: TestClient,
        current_user: User,
        conversation_service_mock: AsyncMock,
    ) -> None:
        # Arrange
        conversation_service_mock.get_messages_page.return_value = MessagePageResponse(
            items=[
                MessageResponse(
                    id=71,
                    conversation_id=1,
                    role="user",
                    content="Первое сообщение",
                    created_at=datetime.now(UTC),
                ),
                MessageResponse(
                    id=72,
                    conversation_id=1,
                    role="assistant",
                    content="Второе сообщение",
                    created_at=datetime.now(UTC),
                ),
            ],
            next_cursor=71,
            has_more=True,
        )

        # Act
        response = client.get(
            "/conversations/1/messages",
            params={
                "limit": 30,
                "before_id": 100,
            },
        )

        # Assert
        assert response.status_code == 200

        conversation_service_mock.get_messages_page.assert_awaited_once_with(
            conversation_id=1,
            user_id=current_user.id,
            limit=30,
            before_id=100,
        )

        response_data = response.json()

        assert len(response_data["items"]) == 2
        assert response_data["next_cursor"] == 71
        assert response_data["has_more"] is True


def test_get_messages_returns_404_for_foreign_conversation(
    client: TestClient,
    conversation_service_mock: AsyncMock,
) -> None:
    # Arrange
    conversation_service_mock.get_messages_page.side_effect = (
        ConversationNotFoundError()
    )

    # Act
    response = client.get(
        "/conversations/999/messages",
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": ErrorCode.CONVERSATION_NOT_FOUND,
            "message": CONVERSATION_NOT_FOUND_ERROR_MESSAGE,
        }
    }
