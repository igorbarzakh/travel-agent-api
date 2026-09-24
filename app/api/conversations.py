from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.api.dependencies import (
    get_conversation_service,
    get_current_user,
)
from app.api.responses import LLM_ERROR_RESPONSES
from app.core.error_codes import ErrorCode
from app.core.exceptions import (
    ConversationNotFoundError,
    EmptyLLMResponseError,
    LLMRequestError,
)
from app.db.models.user import User
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    MessageCreateRequest,
    MessagePageResponse,
    MessageResponse,
)
from app.schemas.error import ErrorDetail
from app.services.conversation import ConversationService


router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.get(
    "",
    response_model=list[ConversationResponse],
)
async def get_conversations(
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> list[ConversationResponse]:
    return await service.get_user_conversations(
        user_id=current_user.id,
    )


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=201,
)
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    return await service.create_conversation(
        user_id=current_user.id,
        title=request.title,
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=MessagePageResponse,
)
async def get_messages(
    conversation_id: int,
    limit: int = Query(default=30, ge=1, le=100),
    before_id: int | None = Query(default=None, ge=1),
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> MessagePageResponse:
    try:
        return await service.get_messages_page(
            conversation_id=conversation_id,
            user_id=current_user.id,
            limit=limit,
            before_id=before_id,
        )
    except ConversationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code=ErrorCode.CONVERSATION_NOT_FOUND,
                message=str(error),
            ).model_dump(),
        ) from error


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    responses=LLM_ERROR_RESPONSES,
)
async def send_message(
    conversation_id: int,
    request: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> MessageResponse:
    try:
        return await service.send_message(
            conversation_id=conversation_id,
            user_id=current_user.id,
            content=request.content,
        )
    except ConversationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code=ErrorCode.CONVERSATION_NOT_FOUND,
                message=str(error),
            ).model_dump(),
        ) from error
    except (EmptyLLMResponseError, LLMRequestError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorDetail(
                code=(
                    ErrorCode.EMPTY_LLM_RESPONSE
                    if isinstance(error, EmptyLLMResponseError)
                    else ErrorCode.LLM_REQUEST_FAILED
                ),
                message=str(error),
            ).model_dump(),
        ) from error
