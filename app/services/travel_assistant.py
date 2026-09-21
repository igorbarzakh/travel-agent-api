from openai import AsyncOpenAI, APIError
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from app.core.config import settings
from app.core.prompts import TRAVEL_SYSTEM_PROMPT
from app.core.exceptions import EmptyLLMResponseError, LLMRequestError


class TravelAssistantService:
    def __init__(self):
       self._client = AsyncOpenAI(
           base_url=settings.groq_url,
           api_key=settings.groq_api_key,
       )
       self._model = settings.groq_model

    async def get_recommendation(self, query: str) -> str:
       try:
           completion = await self._client.chat.completions.create(
               model=self._model,
               messages=[
                   ChatCompletionSystemMessageParam(
                       role="system",
                       content=TRAVEL_SYSTEM_PROMPT,
                   ),
                   ChatCompletionUserMessageParam(
                       role="user",
                       content=query,
                   ),
               ]
           )

       except APIError as error:
           raise LLMRequestError() from error

       if not completion.choices:
           raise EmptyLLMResponseError()

       content = completion.choices[0].message.content

       if content is None or not content.strip():
           raise EmptyLLMResponseError()

       return content.strip()


    async def close(self) -> None:
        await self._client.close()
