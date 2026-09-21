class LLMError(RuntimeError):
    """Базовая ошибка при работе с LLM."""


class EmptyLLMResponseError(LLMError):
    def __init__(self) -> None:
        super().__init__("LLM вернула пустой ответ")


class LLMRequestError(LLMError):
    def __init__(self) -> None:
        super().__init__("Не удалось получить ответ от LLM")