from abc import ABC, abstractmethod

from app.models.refresh_token_model import RefreshToken


class RefreshTokenRepositoryInterface(ABC):

    @abstractmethod
    async def get_valid(
        self,
        jti: str,
        user_id: int,
        token_hash: str,
    ) -> RefreshToken | None:
        pass

    @abstractmethod
    async def create(
        self,
        refresh_token: RefreshToken,
    ) -> RefreshToken:
        pass

    @abstractmethod
    async def revoke(
        self,
        refresh_token: RefreshToken,
    ) -> None:
        pass