from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chat import ChatMessage


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(
        min_length=1,
        max_length=2000,
        description="Вопрос пользователя",
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
    )


class RecommendationResponse(BaseModel):
    answer: str


class StreamRecommendationMessage(BaseModel):
    text: str
