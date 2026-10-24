from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from app.config.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)
from app.models.user_model import User
from app.schemas.auth_schema import UserRegister


password_hash = PasswordHash.recommended()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, data: UserRegister) -> User:
        statement = select(User).where(User.email == data.email)
        result = await self.db.execute(statement)

        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        user = User(
            email=str(data.email),
            hashed_password=password_hash.hash(data.password),
            role="staff",
            is_active=True,
        )

        self.db.add(user)

        try:
            await self.db.commit()
            await self.db.refresh(user)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        return user

    async def authenticate_user(
        self, email: str, password: str
    ) -> User:
        statement = select(User).where(User.email == email)
        result = await self.db.execute(statement)
        user = result.scalar_one_or_none()

        if (
            user is None
            or not password_hash.verify(password, user.hashed_password)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        return user

    def create_access_token(self, user: User) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

        payload = {
            "sub": str(user.id),
            "role": user.role,
            "exp": expires_at,
        }

        return jwt.encode(
            payload,
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM,
        )


    