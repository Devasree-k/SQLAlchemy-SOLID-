import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.dependencies.database import get_database
from app.models.user_model import User
from app.repositories.implementations.user_repository import UserRepository


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_database),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)

        if payload.get("type") != "access":
            raise credentials_exception

        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise credentials_exception

    user = await UserRepository(db).get_by_id(user_id)

    if user is None or not user.is_active:
        raise credentials_exception

    return user


def require_roles(*allowed_roles: str):
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return role_checker


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "driver:read", "driver:create", "driver:update", "driver:delete",
        "collection:read", "collection:create",
        "collection:update", "collection:delete",
        "report:read", "user:manage",
    },
    "supervisor": {
        "driver:read", "driver:create", "driver:update",
        "collection:read", "collection:create", "collection:update",
        "report:read",
    },
    "collector": {
        "driver:read",
        "collection:read", "collection:create",
    },
}


def require_permissions(*required_permissions: str):
    async def permission_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_permissions = ROLE_PERMISSIONS.get(
            current_user.role,
            set(),
        )

        if not set(required_permissions).issubset(user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return permission_checker