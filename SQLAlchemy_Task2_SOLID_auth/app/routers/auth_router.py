from typing import Annotated

import jwt

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.dependencies.auth_dependencies import get_current_user
from app.dependencies.database import get_database
from app.dependencies.service_dependencies import get_auth_service
from app.models.user_model import User
from app.schemas.auth_schema import (
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenInfoResponse,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    AuthService,
    AuthenticationError,
    RegistrationConflict,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> User:
    try:
        return await service.register(data)
    except RegistrationConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    try:
        return await service.login(
            username=form_data.username,
            password=form_data.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    try:
        return await service.refresh(data.refresh_token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        ) from exc


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> Response:
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")

        if int(payload["sub"]) != current_user.id:
            raise ValueError("Token belongs to another user")
    except (
        jwt.InvalidTokenError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from exc

    await service.logout(data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.get("/token-info", response_model=TokenInfoResponse)
async def get_token_info(
    current_user: User = Depends(get_current_user),
) -> TokenInfoResponse:
    return TokenInfoResponse(
        user_id=current_user.id,
        role=current_user.role,
        token_type="access",
    )

