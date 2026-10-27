import jwt

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
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
from app.exceptions.custom_exceptions import RegistrationConflict,AuthenticationError


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
            role="driver",
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