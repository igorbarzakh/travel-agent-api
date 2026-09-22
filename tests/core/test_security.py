import jwt
import pytest

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_hash_password_returns_different_value() -> None:
    # Arrange
    password = "secret123"

    # Act
    hashed_password = hash_password(password)

    # Assert
    assert hashed_password != password


def test_verify_password_returns_true_for_correct_password() -> None:
    # Arrange
    password = "secret123"
    hashed_password = hash_password(password)

    # Act
    result = verify_password(password, hashed_password)

    # Assert
    assert result is True


def test_verify_password_returns_false_for_wrong_password() -> None:
    # Arrange
    hashed_password = hash_password("secret123")

    # Act
    result = verify_password("wrong-password", hashed_password)

    # Assert
    assert result is False


def test_create_and_decode_access_token() -> None:
    # Arrange
    user_id = 42

    # Act
    token = create_access_token(user_id)
    decoded_user_id = decode_access_token(token)

    # Assert
    assert decoded_user_id == user_id


def test_decode_access_token_rejects_invalid_token() -> None:
    # Act & Assert
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("invalid-token")
