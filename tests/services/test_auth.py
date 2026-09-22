from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import asyncio
from unittest.mock import AsyncMock
from sqlalchemy.exc import IntegrityError

import pytest

from app.core.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from app.core.security import hash_password, decode_access_token, hash_refresh_token
from app.db.models.user import User
from app.services.auth import AuthService


def test_register_creates_user(
    auth_service: AuthService,
    user_repository: AsyncMock,
) -> None:
    # Arrange
    user_repository.get_by_email.return_value = None
    created_user = User(
        id=1,
        email="user@example.com",
        password_hash="hashed-password",
    )
    user_repository.create.return_value = created_user

    # Act
    result = asyncio.run(
        auth_service.register(
            "user@example.com",
            "secret123",
        )
    )

    # Assert
    assert result is created_user
    user_repository.get_by_email.assert_awaited_once_with("user@example.com")
    user_repository.create.assert_awaited_once()


def test_register_rejects_existing_user(
    auth_service: AuthService,
    user_repository: AsyncMock,
) -> None:
    # Arrange
    user_repository.get_by_email.return_value = User(
        id=1,
        email="user@example.com",
        password_hash="hashed-password",
    )

    # Act & Assert
    with pytest.raises(UserAlreadyExistsError):
        asyncio.run(
            auth_service.register(
                "user@example.com",
                "secret123",
            )
        )

    user_repository.create.assert_not_awaited()


def test_register_wraps_integrity_error(
    auth_service: AuthService,
    user_repository: AsyncMock,
) -> None:
    # Arrange
    user_repository.get_by_email.return_value = None
    integrity_error = IntegrityError(
        statement="INSERT INTO users ...",
        params={},
        orig=Exception("duplicate key"),
    )
    user_repository.create.side_effect = integrity_error

    # Act & Assert
    with pytest.raises(UserAlreadyExistsError) as exc_info:
        asyncio.run(
            auth_service.register(
                "user@example.com",
                "secret123",
            )
        )

    assert exc_info.value.__cause__ is integrity_error


def test_login_returns_tokens(
    auth_service: AuthService,
    user_repository: AsyncMock,
    refresh_session_repository: AsyncMock,
) -> None:
    # Arrange
    password = "secret123"
    user = User(
        id=1,
        email="user@example.com",
        password_hash=hash_password(password),
    )
    user_repository.get_by_email.return_value = user

    # Act
    access_token, refresh_token = asyncio.run(
        auth_service.login(
            "user@example.com",
            password,
        )
    )

    # Assert
    call_args = refresh_session_repository.create.call_args

    assert decode_access_token(access_token) == user.id
    assert refresh_token
    assert call_args.kwargs["user_id"] == user.id
    assert call_args.kwargs["token_hash"] == hash_refresh_token(refresh_token)
    assert call_args.kwargs["expires_at"] is not None


def test_login_rejects_unknown_user(
    auth_service: AuthService,
    user_repository: AsyncMock,
) -> None:
    # Arrange
    user_repository.get_by_email.return_value = None

    # Act & Assert
    with pytest.raises(InvalidCredentialsError):
        asyncio.run(
            auth_service.login(
                "user@example.com",
                "secret123",
            )
        )


def test_login_rejects_wrong_password(
    auth_service: AuthService,
    user_repository: AsyncMock,
) -> None:
    # Arrange
    user = User(
        id=1,
        email="user@example.com",
        password_hash=hash_password("secret123"),
    )
    user_repository.get_by_email.return_value = user

    # Act & Assert
    with pytest.raises(InvalidCredentialsError):
        asyncio.run(
            auth_service.login(
                "user@example.com",
                "wrong-password",
            )
        )


def test_refresh_returns_new_access_token(
    auth_service: AuthService,
    refresh_session_repository: AsyncMock,
) -> None:
    # Arrange
    refresh_token = "refresh-token"
    refresh_session_repository.get_by_token_hash.return_value = SimpleNamespace(
        user_id=1,
        revoked_at=None,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    # Act
    access_token = asyncio.run(auth_service.refresh(refresh_token))

    # Assert
    assert decode_access_token(access_token) == 1


def test_refresh_rejects_unknown_token(
    auth_service: AuthService,
    refresh_session_repository: AsyncMock,
) -> None:
    # Arrange
    refresh_session_repository.get_by_token_hash.return_value = None

    # Act & Assert
    with pytest.raises(InvalidRefreshTokenError):
        asyncio.run(auth_service.refresh("invalid-token"))


def test_refresh_rejects_expired_token(
    auth_service: AuthService,
    refresh_session_repository: AsyncMock,
) -> None:
    # Arrange
    refresh_session_repository.get_by_token_hash.return_value = SimpleNamespace(
        user_id=1,
        revoked_at=None,
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )

    # Act & Assert
    with pytest.raises(InvalidRefreshTokenError):
        asyncio.run(auth_service.refresh("expired-token"))


def test_refresh_rejects_revoked_token(
    auth_service: AuthService,
    refresh_session_repository: AsyncMock,
) -> None:
    # Arrange
    refresh_session_repository.get_by_token_hash.return_value = SimpleNamespace(
        user_id=1,
        revoked_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    # Act & Assert
    with pytest.raises(InvalidRefreshTokenError):
        asyncio.run(auth_service.refresh("revoked-token"))


def test_logout_revokes_refresh_session(
    auth_service: AuthService,
    refresh_session_repository: AsyncMock,
) -> None:
    # Arrange
    refresh_session = SimpleNamespace(
        revoked_at=None,
    )
    refresh_session_repository.get_by_token_hash.return_value = refresh_session

    # Act
    asyncio.run(auth_service.logout("refresh-token"))

    # Assert
    refresh_session_repository.revoke.assert_awaited_once_with(refresh_session)


def test_logout_rejects_unknown_token(
    auth_service: AuthService,
    refresh_session_repository: AsyncMock,
) -> None:
    # Arrange
    refresh_session_repository.get_by_token_hash.return_value = None

    # Act & Assert
    with pytest.raises(InvalidRefreshTokenError):
        asyncio.run(auth_service.logout("invalid-token"))


def test_logout_rejects_revoked_token(
    auth_service: AuthService,
    refresh_session_repository: AsyncMock,
) -> None:
    # Arrange
    refresh_session_repository.get_by_token_hash.return_value = SimpleNamespace(
        revoked_at=datetime.now(UTC),
    )

    # Act & Assert
    with pytest.raises(InvalidRefreshTokenError):
        asyncio.run(auth_service.logout("revoked-token"))
