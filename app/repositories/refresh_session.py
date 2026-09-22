from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.refresh_session import RefreshSession


class RefreshSessionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshSession:
        refresh_session = RefreshSession(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self._session.add(refresh_session)
        await self._session.commit()
        await self._session.refresh(refresh_session)

        return refresh_session

    async def get_by_token_hash(
        self,
        token_hash: str,
    ) -> RefreshSession | None:
        result = await self._session.execute(
            select(RefreshSession).where(RefreshSession.token_hash == token_hash)
        )

        return result.scalar_one_or_none()

    async def revoke(
        self,
        refresh_session: RefreshSession,
    ) -> None:
        refresh_session.revoked_at = datetime.now(UTC)
        await self._session.commit()
