from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_travel_service
from app.schemas.recommendation import RecommendationResponse, RecommendationRequest
from app.core.exceptions import EmptyLLMResponseError, LLMRequestError
from app.services.travel_assistant import TravelAssistantService

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)


@router.post("", response_model=RecommendationResponse)
async def create_recommendation(
    request: RecommendationRequest,
    service: TravelAssistantService = Depends(get_travel_service)
) -> RecommendationResponse:
    try:
        answer = await service.get_recommendation(request.query)
    except (EmptyLLMResponseError, LLMRequestError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return RecommendationResponse(answer=answer)
