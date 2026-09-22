from datetime import UTC, datetime
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_refresh_token_expires_at,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.models.user import User
from app.repositories.user import UserRepository
from app.repositories.refresh_session import RefreshSessionRepository


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_session_repository: RefreshSessionRepository,
    ):
        self._user_repository = user_repository
        self._refresh_session_repository = refresh_session_repository

    async def register(
        self,
        email: str,
        password: str,
    ) -> User:
        existing_user = await self._user_repository.get_by_email(email)

        if existing_user is not None:
            raise UserAlreadyExistsError()

        password_hash = hash_password(password)

        try:
            return await self._user_repository.create(
                email=email,
                password_hash=password_hash,
            )
        except IntegrityError as error:
            raise UserAlreadyExistsError() from error

    async def login(
        self,
        email: str,
        password: str,
    ) -> tuple[str, str]:
        user = await self._user_repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token()

        await self._refresh_session_repository.create(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=get_refresh_token_expires_at(),
        )

        return access_token, refresh_token

    async def refresh(self, refresh_token: str) -> str:
        token_hash = hash_refresh_token(refresh_token)

        refresh_session = await self._refresh_session_repository.get_by_token_hash(
            token_hash
        )

        if refresh_session is None:
            raise InvalidRefreshTokenError()

        if refresh_session.revoked_at is not None:
            raise InvalidRefreshTokenError()

        if refresh_session.expires_at <= datetime.now(UTC):
            raise InvalidRefreshTokenError()

        return create_access_token(refresh_session.user_id)

    async def logout(self, refresh_token: str) -> None:
        token_hash = hash_refresh_token(refresh_token)

        refresh_session = await self._refresh_session_repository.get_by_token_hash(
            token_hash
        )

        if refresh_session is None:
            raise InvalidRefreshTokenError()

        if refresh_session.revoked_at is not None:
            raise InvalidRefreshTokenError()

        await self._refresh_session_repository.revoke(refresh_session)
