from app.core.exceptions import ConversationNotFoundError
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.schemas.chat import ChatMessage
from app.schemas.conversation import (
    ConversationResponse,
    MessagePageResponse,
    MessageResponse,
)
from app.services.travel_assistant import TravelAssistantService


class ConversationService:
    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        travel_service: TravelAssistantService,
    ):
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._travel_service = travel_service

    async def get_messages_page(
        self,
        conversation_id: int,
        user_id: int,
        limit: int = 30,
        before_id: int | None = None,
    ) -> MessagePageResponse:
        conversation = await self._conversation_repository.get_by_id(conversation_id)

        if conversation is None or conversation.user_id != user_id:
            raise ConversationNotFoundError()

        messages, has_more = await self._message_repository.get_page_by_conversation_id(
            conversation_id=conversation_id,
            limit=limit,
            before_id=before_id,
        )

        next_cursor = messages[0].id if has_more and messages else None

        return MessagePageResponse(
            items=[
                MessageResponse(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    role=message.role,
                    content=message.content,
                    created_at=message.created_at,
                )
                for message in messages
            ],
            next_cursor=next_cursor,
            has_more=has_more,
        )

    async def create_conversation(
        self,
        user_id: int,
        title: str | None = None,
    ) -> ConversationResponse:
        conversation = await self._conversation_repository.create(
            user_id=user_id,
            title=title,
        )

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    async def get_user_conversations(
        self,
        user_id: int,
    ) -> list[ConversationResponse]:
        conversations = await self._conversation_repository.get_by_user_id(user_id)

        return [
            ConversationResponse(
                id=conversation.id,
                user_id=conversation.user_id,
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )
            for conversation in conversations
        ]

    async def send_message(
        self,
        conversation_id: int,
        user_id: int,
        content: str,
    ) -> MessageResponse:
        conversation = await self._conversation_repository.get_by_id(conversation_id)

        if conversation is None or conversation.user_id != user_id:
            raise ConversationNotFoundError()

        user_message = await self._message_repository.create(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

        recent_messages = await self._message_repository.get_recent_by_conversation_id(
            conversation_id=conversation_id,
            limit=21,
        )

        history = [
            ChatMessage(
                role=message.role,
                content=message.content,
            )
            for message in recent_messages
            if message.id != user_message.id
        ][-20:]

        answer = await self._travel_service.get_recommendation(
            query=content,
            history=history,
        )

        assistant_message = await self._message_repository.create(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
        )

        return MessageResponse(
            id=assistant_message.id,
            conversation_id=assistant_message.conversation_id,
            role=assistant_message.role,
            content=assistant_message.content,
            created_at=assistant_message.created_at,
        )
