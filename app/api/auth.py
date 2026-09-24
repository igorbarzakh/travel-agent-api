from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie

from app.api.dependencies import get_auth_service, get_refresh_token
from app.core.config import settings
from app.core.exceptions import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UserAlreadyExistsError,
)

from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.auth import AuthService
from app.api.responses import (
    LOGIN_RESPONSES,
    LOGOUT_RESPONSES,
    REFRESH_RESPONSES,
    REGISTER_RESPONSES,
)
from app.core.error_codes import ErrorCode
from app.schemas.error import ErrorDetail


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses=REGISTER_RESPONSES,
)
async def register(
    request: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    try:
        user = await service.register(
            request.email,
            request.password,
        )
    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorDetail(
                code=ErrorCode.USER_ALREADY_EXISTS,
                message=str(error),
            ).model_dump(),
        ) from error

    return RegisterResponse(
        id=user.id,
        email=user.email,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    responses=LOGIN_RESPONSES,
)
async def login(
    request: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        access_token, refresh_token = await service.login(
            request.email,
            request.password,
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorDetail(
                code=ErrorCode.INVALID_CREDENTIALS,
                message=str(error),
            ).model_dump(),
        ) from error

    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/auth",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )

    return AuthResponse(
        access_token=access_token,
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    responses=REFRESH_RESPONSES,
)
async def refresh(
    refresh_token: str = Depends(get_refresh_token),
    service: AuthService = Depends(get_auth_service),
) -> RefreshResponse:
    try:
        access_token = await service.refresh(refresh_token)
    except InvalidRefreshTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorDetail(
                code=ErrorCode.INVALID_REFRESH_TOKEN,
                message=str(error),
            ).model_dump(),
        ) from error

    return RefreshResponse(
        access_token=access_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=LOGOUT_RESPONSES,
)
async def logout(
    response: Response,
    refresh_token: str = Depends(get_refresh_token),
    service: AuthService = Depends(get_auth_service),
) -> None:
    try:
        await service.logout(refresh_token)
    except InvalidRefreshTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorDetail(
                code=ErrorCode.INVALID_REFRESH_TOKEN,
                message=str(error),
            ).model_dump(),
        ) from error

    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path="/auth",
    )
