
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import Session, selectinload

from models.driver_model import Driver

from interfaces.driver_repository_interface import DriverRepositoryInterface

class DriverRepository(DriverRepositoryInterface):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, driver: Driver) -> Driver:
        self.db.add(driver)     #No await because it is synchrnous session-state operation.
        await self.db.flush()
        return driver

    async def get_by_id(self, driver_id: int):
        return await self.db.get(Driver, driver_id)

    async def get_all(self):
        statement = select(Driver).order_by(Driver.id)
        result = await self.db.scalars(statement)
        return list(result.all())

    async def get_with_collections(self, driver_id: int):
        statement = (
            select(Driver)
            .options(selectinload(Driver.collections))
            .where(Driver.id == driver_id)
        )
        result = await self.db.scalars(statement)
        return result.first()

    async def phone_exists(
        self,
        phone: str,
        exclude_driver_id: int | None = None,
    ) -> bool:
        statement = select(Driver.id).where(Driver.phone == phone)

        if exclude_driver_id is not None:
            statement = statement.where(
                Driver.id != exclude_driver_id
            )

        return (
            await self.db.scalar(statement)
        ) is not None

