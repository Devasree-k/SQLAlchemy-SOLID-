from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from models.driver_model import Driver


class DriverRepositoryInterface(ABC):

    @abstractmethod
    async def create(self, driver: Driver) -> Driver:
        pass

    @abstractmethod
    async def get_all(self) -> list[Driver]:
        pass

    @abstractmethod
    async def get_by_id(self, driver_id: int) -> Driver | None:
        pass

    @abstractmethod
    async def get_with_collections(
        self, driver_id: int
    ) -> Driver | None:
        pass

    # @abstractmethod
    # async def get_driver_report(
    #     self,
    #     start_date: date | None = None,
    #     end_date: date | None = None,
    # ) -> list[dict[str, Any]]:
    #     pass