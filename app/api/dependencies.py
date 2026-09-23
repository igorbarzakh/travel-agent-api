import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.travel_assistant import TravelAssistantService
from app.db.dependencies import get_db_session
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.repositories.refresh_session import RefreshSessionRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.services.conversation import ConversationService

from app.core.security import decode_access_token
from app.db.models.user import User

from app.core.error_codes import ErrorCode
from app.core.messages import INVALID_ACCESS_TOKEN_ERROR_MESSAGE
from app.schemas.error import ErrorDetail


bearer_scheme = HTTPBearer()


def _invalid_access_token_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ErrorDetail(
            code=ErrorCode.INVALID_ACCESS_TOKEN,
            message=INVALID_ACCESS_TOKEN_ERROR_MESSAGE,
        ).model_dump(),
    )


def get_travel_service(request: Request) -> TravelAssistantService:
    return request.app.state.travel_service


def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuthService:
    user_repository = UserRepository(session)
    refresh_session_repository = RefreshSessionRepository(session)

    return AuthService(
        user_repository,
        refresh_session_repository,
    )


def get_conversation_service(
    session: AsyncSession = Depends(get_db_session),
    travel_service: TravelAssistantService = Depends(get_travel_service),
) -> ConversationService:
    conversation_repository = ConversationRepository(session)
    message_repository = MessageRepository(session)

    return ConversationService(
        conversation_repository,
        message_repository,
        travel_service,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    try:
        user_id = decode_access_token(credentials.credentials)
    except (jwt.InvalidTokenError, ValueError):
        raise _invalid_access_token_exception()

    user_repository = UserRepository(session)
    user = await user_repository.get_by_id(user_id)

    if user is None:
        raise _invalid_access_token_exception()

    return user
