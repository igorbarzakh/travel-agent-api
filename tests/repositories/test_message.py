import asyncio
from collections.abc import Iterator
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.user import User
from app.repositories.message import MessageRepository


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db_session:
        db_session.add(User(id=1, email="user@example.com", password_hash="hash"))
        db_session.flush()
        db_session.add_all(
            [
                Conversation(
                    id=1, user_id=1, updated_at=datetime(2020, 1, 1, tzinfo=UTC)
                ),
                Conversation(
                    id=2, user_id=1, updated_at=datetime(2021, 1, 1, tzinfo=UTC)
                ),
            ]
        )
        db_session.commit()
        yield db_session
    engine.dispose()


@pytest.fixture
def repository(session: Session) -> MessageRepository:
    # Run real SQL against SQLite through the repository's async interface.
    async_session = MagicMock(spec=AsyncSession)
    async_session.add.side_effect = session.add
    async_session.execute = AsyncMock(side_effect=session.execute)
    async_session.commit = AsyncMock(side_effect=session.commit)
    async_session.refresh = AsyncMock(side_effect=session.refresh)
    return MessageRepository(async_session)


@pytest.mark.parametrize("role", ["user", "assistant"])
def test_create_updates_only_target_conversation(
    session: Session,
    repository: MessageRepository,
    role: str,
) -> None:
    message = asyncio.run(repository.create(1, role, "Новое сообщение"))

    session.expire_all()
    assert session.get(Message, message.id).content == "Новое сообщение"
    assert session.get(Conversation, 1).updated_at.date() > date(2021, 1, 1)
    assert session.get(Conversation, 2).updated_at.date() == date(2021, 1, 1)
    conversations = session.scalars(
        select(Conversation).order_by(Conversation.updated_at.desc())
    ).all()
    assert [conversation.id for conversation in conversations] == [1, 2]


def test_create_rolls_back_message_and_activity_when_commit_fails(
    session: Session,
    repository: MessageRepository,
) -> None:
    def fail_commit(db_session: Session) -> None:
        db_session.flush()
        assert db_session.scalar(select(Message.id)) is not None
        assert db_session.get(Conversation, 1).updated_at.date() > date(2021, 1, 1)
        raise RuntimeError("Commit failed")

    event.listen(session, "before_commit", fail_commit)

    with pytest.raises(RuntimeError, match="Commit failed"):
        asyncio.run(repository.create(1, "user", "Новое сообщение"))

    session.rollback()
    assert session.scalar(select(Message.id)) is None
    assert session.get(Conversation, 1).updated_at.date() == date(2020, 1, 1)
