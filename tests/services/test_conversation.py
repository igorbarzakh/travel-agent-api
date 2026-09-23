import pytest
import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.schemas.chat import ChatMessage
from app.services.conversation import ConversationService
from app.core.exceptions import ConversationNotFoundError


def test_send_message_saves_user_and_assistant_messages(
    conversation_service: ConversationService,
    conversation_repository: AsyncMock,
    message_repository: AsyncMock,
    travel_service_mock: AsyncMock,
) -> None:
    # Arrange
    conversation_repository.get_by_id.return_value = SimpleNamespace(
        id=1,
        user_id=10,
    )

    user_message = SimpleNamespace(
        id=101,
        conversation_id=1,
        role="user",
        content="Куда поехать в ноябре?",
        created_at=datetime.now(UTC),
    )

    assistant_message = SimpleNamespace(
        id=102,
        conversation_id=1,
        role="assistant",
        content="Можно рассмотреть Японию.",
        created_at=datetime.now(UTC),
    )

    message_repository.create.side_effect = [
        user_message,
        assistant_message,
    ]

    message_repository.get_recent_by_conversation_id.return_value = [
        user_message,
    ]

    travel_service_mock.get_recommendation.return_value = "Можно рассмотреть Японию."

    # Act
    result = asyncio.run(
        conversation_service.send_message(
            conversation_id=1,
            user_id=10,
            content="Куда поехать в ноябре?",
        )
    )

    # Assert
    assert result.id == 102
    assert result.conversation_id == 1
    assert result.role == "assistant"
    assert result.content == "Можно рассмотреть Японию."

    assert message_repository.create.await_count == 2

    travel_service_mock.get_recommendation.assert_awaited_once_with(
        query="Куда поехать в ноябре?",
        history=[],
    )


def test_send_message_rejects_unknown_conversation(
    conversation_service: ConversationService,
    conversation_repository: AsyncMock,
    message_repository: AsyncMock,
    travel_service_mock: AsyncMock,
) -> None:
    # Arrange
    conversation_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(ConversationNotFoundError):
        asyncio.run(
            conversation_service.send_message(
                conversation_id=1,
                user_id=10,
                content="Куда поехать?",
            )
        )

    message_repository.create.assert_not_awaited()
    travel_service_mock.get_recommendation.assert_not_awaited()


def test_send_message_rejects_foreign_conversation(
    conversation_service: ConversationService,
    conversation_repository: AsyncMock,
    message_repository: AsyncMock,
    travel_service_mock: AsyncMock,
) -> None:
    # Arrange
    conversation_repository.get_by_id.return_value = SimpleNamespace(
        id=1,
        user_id=99,
    )

    # Act & Assert
    with pytest.raises(ConversationNotFoundError):
        asyncio.run(
            conversation_service.send_message(
                conversation_id=1,
                user_id=10,
                content="Куда поехать?",
            )
        )

    message_repository.create.assert_not_awaited()
    travel_service_mock.get_recommendation.assert_not_awaited()


def test_send_message_builds_history_from_recent_messages(
    conversation_service: ConversationService,
    conversation_repository: AsyncMock,
    message_repository: AsyncMock,
    travel_service_mock: AsyncMock,
) -> None:
    # Arrange
    conversation_repository.get_by_id.return_value = SimpleNamespace(
        id=1,
        user_id=10,
    )

    first_user_message = SimpleNamespace(
        id=1,
        conversation_id=1,
        role="user",
        content="Хочу в Японию",
        created_at=datetime.now(UTC),
    )

    first_assistant_message = SimpleNamespace(
        id=2,
        conversation_id=1,
        role="assistant",
        content="Когда планируете поездку?",
        created_at=datetime.now(UTC),
    )

    current_user_message = SimpleNamespace(
        id=3,
        conversation_id=1,
        role="user",
        content="В ноябре",
        created_at=datetime.now(UTC),
    )

    assistant_message = SimpleNamespace(
        id=4,
        conversation_id=1,
        role="assistant",
        content="В ноябре можно рассмотреть Токио и Киото.",
        created_at=datetime.now(UTC),
    )

    message_repository.create.side_effect = [
        current_user_message,
        assistant_message,
    ]

    message_repository.get_recent_by_conversation_id.return_value = [
        first_user_message,
        first_assistant_message,
        current_user_message,
    ]

    travel_service_mock.get_recommendation.return_value = (
        "В ноябре можно рассмотреть Токио и Киото."
    )

    # Act
    asyncio.run(
        conversation_service.send_message(
            conversation_id=1,
            user_id=10,
            content="В ноябре",
        )
    )

    # Assert
    travel_service_mock.get_recommendation.assert_awaited_once_with(
        query="В ноябре",
        history=[
            ChatMessage(
                role="user",
                content="Хочу в Японию",
            ),
            ChatMessage(
                role="assistant",
                content="Когда планируете поездку?",
            ),
        ],
    )


def test_get_messages_page_returns_paginated_messages(
    conversation_service: ConversationService,
    conversation_repository: AsyncMock,
    message_repository: AsyncMock,
) -> None:
    # Arrange
    conversation_repository.get_by_id.return_value = SimpleNamespace(
        id=1,
        user_id=10,
    )

    messages = [
        SimpleNamespace(
            id=71,
            conversation_id=1,
            role="user",
            content="Первое сообщение",
            created_at=datetime.now(UTC),
        ),
        SimpleNamespace(
            id=72,
            conversation_id=1,
            role="assistant",
            content="Второе сообщение",
            created_at=datetime.now(UTC),
        ),
    ]

    message_repository.get_page_by_conversation_id.return_value = (
        messages,
        True,
    )

    # Act
    result = asyncio.run(
        conversation_service.get_messages_page(
            conversation_id=1,
            user_id=10,
            limit=30,
            before_id=None,
        )
    )

    # Assert
    assert len(result.items) == 2
    assert result.items[0].id == 71
    assert result.items[1].id == 72
    assert result.next_cursor == 71
    assert result.has_more is True

    message_repository.get_page_by_conversation_id.assert_awaited_once_with(
        conversation_id=1,
        limit=30,
        before_id=None,
    )


def test_get_messages_page_rejects_foreign_conversation(
    conversation_service: ConversationService,
    conversation_repository: AsyncMock,
    message_repository: AsyncMock,
) -> None:
    # Arrange
    conversation_repository.get_by_id.return_value = SimpleNamespace(
        id=1,
        user_id=99,
    )

    # Act & Assert
    with pytest.raises(ConversationNotFoundError):
        asyncio.run(
            conversation_service.get_messages_page(
                conversation_id=1,
                user_id=10,
            )
        )

    message_repository.get_page_by_conversation_id.assert_not_awaited()


def test_get_messages_page_returns_no_cursor_when_no_more_messages(
    conversation_service: ConversationService,
    conversation_repository: AsyncMock,
    message_repository: AsyncMock,
) -> None:
    # Arrange
    conversation_repository.get_by_id.return_value = SimpleNamespace(
        id=1,
        user_id=10,
    )

    message_repository.get_page_by_conversation_id.return_value = (
        [
            SimpleNamespace(
                id=1,
                conversation_id=1,
                role="user",
                content="Первое сообщение",
                created_at=datetime.now(UTC),
            )
        ],
        False,
    )

    # Act
    result = asyncio.run(
        conversation_service.get_messages_page(
            conversation_id=1,
            user_id=10,
        )
    )

    # Assert
    assert result.next_cursor is None
    assert result.has_more is False


def test_get_messages_page_returns_empty_page(
    conversation_service: ConversationService,
    conversation_repository: AsyncMock,
    message_repository: AsyncMock,
) -> None:
    # Arrange
    conversation_repository.get_by_id.return_value = SimpleNamespace(
        id=1,
        user_id=10,
    )
    message_repository.get_page_by_conversation_id.return_value = (
        [],
        False,
    )

    # Act
    result = asyncio.run(
        conversation_service.get_messages_page(
            conversation_id=1,
            user_id=10,
        )
    )

    # Assert
    assert result.items == []
    assert result.next_cursor is None
    assert result.has_more is False
