from app.core.messages import (
    EMPTY_LLM_RESPONSE_ERROR_MESSAGE,
    LLM_REQUEST_ERROR_MESSAGE,
)


class LLMError(RuntimeError):
    """Базовая ошибка при работе с LLM."""


class EmptyLLMResponseError(LLMError):
    def __init__(self) -> None:
        super().__init__(EMPTY_LLM_RESPONSE_ERROR_MESSAGE)


class LLMRequestError(LLMError):
    def __init__(self) -> None:
        super().__init__(LLM_REQUEST_ERROR_MESSAGE)
