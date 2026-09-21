from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.responses import (
    STREAM_RECOMMENDATION_RESPONSES,
    RECOMMENDATION_RESPONSES
)
from app.api.dependencies import get_travel_service
from app.schemas.recommendation import (
    RecommendationResponse,
    RecommendationRequest,
    StreamRecommendationMessage,
)
from app.core.exceptions import EmptyLLMResponseError, LLMRequestError
from app.services.travel_assistant import TravelAssistantService
from app.core.error_codes import ErrorCode
from app.schemas.error import ErrorDetail


def _get_error_detail(
    error: EmptyLLMResponseError | LLMRequestError,
) -> ErrorDetail:
    return ErrorDetail(
        code=(
            ErrorCode.EMPTY_LLM_RESPONSE
            if isinstance(error, EmptyLLMResponseError)
            else ErrorCode.LLM_REQUEST_FAILED
        ),
        message=str(error),
    )


router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)


@router.post("", response_model=RecommendationResponse, responses=RECOMMENDATION_RESPONSES,)
async def get_recommendation(
    request: RecommendationRequest,
    service: TravelAssistantService = Depends(get_travel_service),
) -> RecommendationResponse:
    try:
        answer = await service.get_recommendation(request.query)
    except (EmptyLLMResponseError, LLMRequestError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_get_error_detail(error).model_dump(),
        ) from error

    return RecommendationResponse(answer=answer)


@router.post("/stream",  response_class=StreamingResponse, responses=STREAM_RECOMMENDATION_RESPONSES)
async def get_stream_recommendation(
    request: RecommendationRequest,
    service: TravelAssistantService = Depends(get_travel_service),
) -> StreamingResponse:
    async def generate() -> AsyncIterator[str]:
        try:
            async for chunk in service.get_stream_recommendation(request.query):
                message = StreamRecommendationMessage(text=chunk)
                yield f"event: message\ndata: {message.model_dump_json()}\n\n"
        except (EmptyLLMResponseError, LLMRequestError) as error:
            error_data = _get_error_detail(error)

            yield f"event: error\ndata: {error_data.model_dump_json()}\n\n"
            return

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )
