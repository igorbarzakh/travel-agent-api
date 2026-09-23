from app.core.messages import (
    EMPTY_LLM_RESPONSE_ERROR_MESSAGE,
    LLM_REQUEST_ERROR_MESSAGE,
    USER_ALREADY_EXISTS_ERROR_MESSAGE,
    INVALID_CREDENTIALS_ERROR_MESSAGE,
    INVALID_REFRESH_TOKEN_ERROR_MESSAGE,
    CONVERSATION_NOT_FOUND_ERROR_MESSAGE,
)


class LLMError(RuntimeError):
    """Базовая ошибка при работе с LLM."""


class EmptyLLMResponseError(LLMError):
    def __init__(self) -> None:
        super().__init__(EMPTY_LLM_RESPONSE_ERROR_MESSAGE)


class LLMRequestError(LLMError):
    def __init__(self) -> None:
        super().__init__(LLM_REQUEST_ERROR_MESSAGE)


class UserAlreadyExistsError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(USER_ALREADY_EXISTS_ERROR_MESSAGE)


class InvalidCredentialsError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(INVALID_CREDENTIALS_ERROR_MESSAGE)


class InvalidRefreshTokenError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(INVALID_REFRESH_TOKEN_ERROR_MESSAGE)


class ConversationNotFoundError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(CONVERSATION_NOT_FOUND_ERROR_MESSAGE)
