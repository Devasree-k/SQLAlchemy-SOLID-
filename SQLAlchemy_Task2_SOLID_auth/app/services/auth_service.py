# from datetime import datetime, timedelta, timezone

# import jwt
# from pwdlib import PasswordHash
# from sqlalchemy import select
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.ext.asyncio import AsyncSession

# from fastapi import HTTPException, status

# from app.config.settings import (
#     ACCESS_TOKEN_EXPIRE_MINUTES,
#     JWT_ALGORITHM,
#     JWT_SECRET_KEY,
# )
# from app.models.user_model import User
# from app.schemas.auth_schema import UserRegister


# password_hash = PasswordHash.recommended()


# class AuthService:
#     def __init__(self, db: AsyncSession):
#         self.db = db

#     async def register_user(self, data: UserRegister) -> User:
#         statement = select(User).where(User.email == data.email)
#         result = await self.db.execute(statement)

#         if result.scalar_one_or_none() is not None:
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="Email is already registered",
#             )

#         user = User(
#             email=str(data.email),
#             hashed_password=password_hash.hash(data.password),
#             role="staff",
#             is_active=True,
#         )

#         self.db.add(user)

#         try:
#             await self.db.commit()
#             await self.db.refresh(user)
#         except IntegrityError:
#             await self.db.rollback()
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="Email is already registered",
#             )

#         return user

#     async def authenticate_user(
#         self, email: str, password: str
#     ) -> User:
#         statement = select(User).where(User.email == email)
#         result = await self.db.execute(statement)
#         user = result.scalar_one_or_none()

#         if (
#             user is None
#             or not password_hash.verify(password, user.hashed_password)
#         ):
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid email or password",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )

#         if not user.is_active:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="User account is inactive",
#             )

#         return user

#     def create_access_token(self, user: User) -> str:
#         expires_at = datetime.now(timezone.utc) + timedelta(
#             minutes=ACCESS_TOKEN_EXPIRE_MINUTES
#         )

#         payload = {
#             "sub": str(user.id),
#             "role": user.role,
#             "exp": expires_at,
#         }

#         return jwt.encode(
#             payload,
#             JWT_SECRET_KEY,
#             algorithm=JWT_ALGORITHM,
#         )


import jwt

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token_model import RefreshToken
from app.models.user_model import User
from app.repositories.interfaces.user_repository_interface import (
    UserRepositoryInterface,
)
from app.repositories.interfaces.refresh_token_repository_interface import (
    RefreshTokenRepositoryInterface,
)
from app.schemas.auth_schema import RegisterRequest


class AuthenticationError(Exception):
    pass


class RegistrationConflict(Exception):
    pass


class AuthService:

    def __init__(
        self,
        db: AsyncSession,
        users: UserRepositoryInterface,
        refresh_tokens: RefreshTokenRepositoryInterface,
    ) -> None:
        self.db = db
        self.users = users
        self.refresh_tokens = refresh_tokens

    async def register(self, data: RegisterRequest) -> User:
        if await self.users.get_by_username(data.username):
            raise RegistrationConflict(
                "Username is already registered."
            )

        email = str(data.email)
        if await self.users.get_by_email(email):
            raise RegistrationConflict(
                "Email is already registered."
            )

        user = User(
            username=data.username,
            email=email,
            hashed_password=hash_password(data.password),
            role="collector",
            is_active=True,
        )

        try:
            await self.users.create(user)
            await self.db.commit()
            await self.db.refresh(user)
        except IntegrityError as exc:
            await self.db.rollback()
            raise RegistrationConflict(
                "Username or email is already registered."
            ) from exc

        return user

    async def authenticate(
        self,
        username: str,
        password: str,
    ) -> User:
        user = await self.users.get_by_username(username)

        if user is None:
            verify_password(password, DUMMY_PASSWORD_HASH)
            raise AuthenticationError(
                "Invalid username or password."
            )

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError(
                "Invalid username or password."
            )

        if not user.is_active:
            raise AuthenticationError(
                "Invalid username or password."
            )

        return user

    async def issue_tokens(self, user: User) -> dict[str, str]:
        access_token = create_access_token(user.id, user.role)

        refresh_token, jti, expires_at = create_refresh_token(
            user.id,
            user.role,
        )

        token_record = RefreshToken(
            jti=jti,
            token_hash=hash_refresh_token(refresh_token),
            user_id=user.id,
            expires_at=expires_at,
            revoked=False,
        )

        await self.refresh_tokens.create(token_record)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def login(
        self,
        username: str,
        password: str,
    ) -> dict[str, str]:
        user = await self.authenticate(username, password)

        try:
            tokens = await self.issue_tokens(user)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return tokens

    async def refresh(
        self,
        raw_refresh_token: str,
    ) -> dict[str, str]:
        try:
            payload = decode_token(raw_refresh_token)
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token.")

            user_id = int(payload["sub"])
            jti = payload["jti"]
            if not isinstance(jti, str):
                raise AuthenticationError("Invalid refresh token.")
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
            raise AuthenticationError(
                "Invalid or expired refresh token."
            ) from exc

        token_record = await self.refresh_tokens.get_valid(
            jti=jti,
            user_id=user_id,
            token_hash=hash_refresh_token(raw_refresh_token),
        )

        if token_record is None:
            raise AuthenticationError(
                "Invalid or expired refresh token."
            )

        user = await self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError(
                "Invalid or expired refresh token."
            )

        try:
            # Invalidate the old refresh token before issuing a new pair.
            await self.refresh_tokens.revoke(token_record)
            tokens = await self.issue_tokens(user)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return tokens

    async def logout(self, raw_refresh_token: str) -> None:
        try:
            payload = decode_token(raw_refresh_token)
            if payload.get("type") != "refresh":
                return

            user_id = int(payload["sub"])
            jti = payload["jti"]
            if not isinstance(jti, str):
                return
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
            return

        token_record = await self.refresh_tokens.get_valid(
            jti=jti,
            user_id=user_id,
            token_hash=hash_refresh_token(raw_refresh_token),
        )

        if token_record is not None:
            await self.refresh_tokens.revoke(token_record)
            await self.db.commit()