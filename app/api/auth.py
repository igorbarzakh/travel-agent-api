from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_auth_service
from app.core.exceptions import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UserAlreadyExistsError,
)
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
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

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=RefreshResponse, responses=REFRESH_RESPONSES)
async def refresh(
    request: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> RefreshResponse:
    try:
        access_token = await service.refresh(request.refresh_token)
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
    "/logout", status_code=status.HTTP_204_NO_CONTENT, responses=LOGOUT_RESPONSES
)
async def logout(
    request: LogoutRequest,
    service: AuthService = Depends(get_auth_service),
) -> None:
    try:
        await service.logout(request.refresh_token)
    except InvalidRefreshTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorDetail(
                code=ErrorCode.INVALID_REFRESH_TOKEN,
                message=str(error),
            ).model_dump(),
        ) from error
