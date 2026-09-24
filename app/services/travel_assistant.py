from collections.abc import AsyncIterator
from typing import cast

from openai import APIError, AsyncOpenAI, AsyncStream
from openai.types.responses import (
    ResponseStreamEvent,
    ResponseTextDeltaEvent,
)

from app.core.config import settings
from app.core.exceptions import EmptyLLMResponseError, LLMRequestError
from app.schemas.chat import ChatMessage
from app.core.prompts import TRAVEL_SYSTEM_PROMPT


class TravelAssistantService:
    def __init__(self):
        self._client = AsyncOpenAI(
            base_url=settings.groq_url,
            api_key=settings.groq_api_key,
        )
        self._model = settings.groq_model

    async def get_recommendation(
        self,
        query: str,
        history: list[ChatMessage],
    ) -> str:
        try:
            input_messages = [message.model_dump() for message in history]
            input_messages.append({"role": "user", "content": query})

            response = await self._client.responses.create(
                model=self._model,
                instructions=TRAVEL_SYSTEM_PROMPT,
                input=input_messages,
            )
        except APIError as error:
            raise LLMRequestError() from error

        content = response.output_text

        if not content or not content.strip():
            raise EmptyLLMResponseError()

        return content.strip()

    async def get_stream_recommendation(
        self,
        query: str,
        history: list[ChatMessage],
    ) -> AsyncIterator[str]:
        try:
            input_messages = [message.model_dump() for message in history]
            input_messages.append({"role": "user", "content": query})

            stream = cast(
                AsyncStream[ResponseStreamEvent],
                await self._client.responses.create(
                    model=self._model,
                    instructions=TRAVEL_SYSTEM_PROMPT,
                    input=input_messages,
                    stream=True,
                ),
            )
            has_content = False

            async for event in stream:
                if not isinstance(event, ResponseTextDeltaEvent):
                    continue

                content = event.delta

                if content:
                    if content.strip():
                        has_content = True

                    yield content
        except APIError as error:
            raise LLMRequestError() from error

        if not has_content:
            raise EmptyLLMResponseError()

    async def close(self) -> None:
        await self._client.close()
