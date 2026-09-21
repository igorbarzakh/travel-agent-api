from pydantic import BaseModel, ConfigDict, Field


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(
        min_length=1,
        max_length=2000,
        description="Вопрос пользователя",
    )


class RecommendationResponse(BaseModel):
    answer: str