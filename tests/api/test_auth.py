from unittest.mock import AsyncMock

from starlette.testclient import TestClient

from app.core.error_codes import ErrorCode
from app.core.exceptions import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UserAlreadyExistsError,
)
from app.core.messages import (
    INVALID_CREDENTIALS_ERROR_MESSAGE,
    INVALID_REFRESH_TOKEN_ERROR_MESSAGE,
    MISSING_REFRESH_TOKEN_ERROR_MESSAGE,
    USER_ALREADY_EXISTS_ERROR_MESSAGE,
)
from app.db.models.user import User
from app.core.config import settings


def test_register_returns_created_user(
    client: TestClient,
    auth_service_mock: AsyncMock,
) -> None:
    # Arrange
    auth_service_mock.register.return_value = User(
        id=1,
        email="user@example.com",
        password_hash="hashed-password",
    )

    # Act
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "secret123",
        },
    )

    # Assert
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "email": "user@example.com",
    }


def test_register_returns_409_for_existing_user(
    client: TestClient,
    auth_service_mock: AsyncMock,
) -> None:
    # Arrange
    auth_service_mock.register.side_effect = UserAlreadyExistsError()

    # Act
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "secret123",
        },
    )

    # Assert
    assert response.status_code == 409
    assert response.json() == {
        "detail": {
            "code": ErrorCode.USER_ALREADY_EXISTS,
            "message": USER_ALREADY_EXISTS_ERROR_MESSAGE,
        }
    }


def test_login_returns_access_token_and_sets_refresh_cookie(
    client: TestClient,
    auth_service_mock: AsyncMock,
) -> None:
    # Arrange
    auth_service_mock.login.return_value = (
        "access-token",
        "refresh-token",
    )

    # Act
    response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "secret123",
        },
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "access_token": "access-token",
        "token_type": "bearer",
    }

    assert response.cookies.get(settings.refresh_cookie_name) == "refresh-token"

    set_cookie = response.headers["set-cookie"]

    assert f"{settings.refresh_cookie_name}=refresh-token" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Path=/auth" in set_cookie
    assert "Max-Age=" in set_cookie


def test_login_returns_401_for_invalid_credentials(
    client: TestClient,
    auth_service_mock: AsyncMock,
) -> None:
    # Arrange
    auth_service_mock.login.side_effect = InvalidCredentialsError()

    # Act
    response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "wrong-password",
        },
    )

    # Assert
    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "code": ErrorCode.INVALID_CREDENTIALS,
            "message": INVALID_CREDENTIALS_ERROR_MESSAGE,
        }
    }


def test_refresh_returns_new_access_token(
    client: TestClient,
    auth_service_mock: AsyncMock,
) -> None:
    # Arrange
    client.cookies.set(
        settings.refresh_cookie_name,
        "refresh-token",
        path="/auth",
    )
    auth_service_mock.refresh.return_value = "new-access-token"

    # Act
    response = client.post("/auth/refresh")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new-access-token",
        "token_type": "bearer",
    }
    auth_service_mock.refresh.assert_awaited_once_with("refresh-token")


def test_refresh_returns_401_for_invalid_token(
    client: TestClient,
    auth_service_mock: AsyncMock,
) -> None:
    # Arrange
    client.cookies.set(
        settings.refresh_cookie_name,
        "invalid-token",
        path="/auth",
    )
    auth_service_mock.refresh.side_effect = InvalidRefreshTokenError()

    # Act
    response = client.post("/auth/refresh")

    # Assert
    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "code": ErrorCode.INVALID_REFRESH_TOKEN,
            "message": INVALID_REFRESH_TOKEN_ERROR_MESSAGE,
        }
    }
    auth_service_mock.refresh.assert_awaited_once_with("invalid-token")


def test_refresh_returns_401_without_refresh_cookie(
    client: TestClient,
    auth_service_mock: AsyncMock,
) -> None:
    # Act
    response = client.post("/auth/refresh")

    # Assert
    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "code": ErrorCode.MISSING_REFRESH_TOKEN,
            "message": MISSING_REFRESH_TOKEN_ERROR_MESSAGE,
        }
    }

    auth_service_mock.refresh.assert_not_awaited()


def test_logout_returns_204_and_deletes_refresh_cookie(
    client: TestClient,
    auth_service_mock: AsyncMock,
) -> None:
    # Arrange
    client.cookies.set(
        settings.refresh_cookie_name,
        "refresh-token",
        path="/auth",
    )

    # Act
    response = client.post("/auth/logout")

    # Assert
    assert response.status_code == 204
    auth_service_mock.logout.assert_awaited_once_with("refresh-token")

    set_cookie = response.headers["set-cookie"]

    assert f"{settings.refresh_cookie_name}=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "Path=/auth" in set_cookie


def test_logout_returns_401_for_invalid_token(
    client: TestClient,
    auth_service_mock: AsyncMock,
) -> None:
    # Arrange
    client.cookies.set(
        settings.refresh_cookie_name,
        "invalid-token",
        path="/auth",
    )
    auth_service_mock.logout.side_effect = InvalidRefreshTokenError()

    # Act
    response = client.post("/auth/logout")

    # Assert
    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "code": ErrorCode.INVALID_REFRESH_TOKEN,
            "message": INVALID_REFRESH_TOKEN_ERROR_MESSAGE,
        }
    }
    auth_service_mock.logout.assert_awaited_once_with("invalid-token")


def test_logout_returns_401_without_refresh_cookie(
    client: TestClient,
    auth_service_mock: AsyncMock,
) -> None:
    # Act
    response = client.post("/auth/logout")

    # Assert
    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "code": ErrorCode.MISSING_REFRESH_TOKEN,
            "message": MISSING_REFRESH_TOKEN_ERROR_MESSAGE,
        }
    }

    auth_service_mock.logout.assert_not_awaited()
