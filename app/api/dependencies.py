from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.travel_assistant import TravelAssistantService
from app.db.dependencies import get_db_session
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.repositories.refresh_session import RefreshSessionRepository


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
