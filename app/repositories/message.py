from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.message import Message


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        conversation_id: int,
        role: str,
        content: str,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)

        return message

    async def get_recent_by_conversation_id(
        self,
        conversation_id: int,
        limit: int = 20,
    ) -> list[Message]:
        result = await self._session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(limit)
        )

        messages = list(result.scalars().all())

        return list(reversed(messages))

    async def get_page_by_conversation_id(
        self,
        conversation_id: int,
        limit: int = 30,
        before_id: int | None = None,
    ) -> tuple[list[Message], bool]:
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(limit + 1)
        )

        if before_id is not None:
            query = query.where(Message.id < before_id)

        result = await self._session.execute(query)

        messages = list(result.scalars().all())

        has_more = len(messages) > limit

        if has_more:
            messages = messages[:limit]

        return list(reversed(messages)), has_more
