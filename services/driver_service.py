
from datetime import date

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.driver_model import Driver
from models.transport_collection_model import TransportCollection
# from repositories.driver_repository import DriverRepository
from interfaces.driver_repository_interface import DriverRepositoryInterface

class DriverService:

    def __init__(self, db: AsyncSession, driver_repository:DriverRepositoryInterface):
        self.db = db
        self.driver_repository = driver_repository

    async def create_driver(self, data):
        driver = Driver(**data.model_dump())

        try:
            await self.driver_repository.create(driver)
            await self.db.commit()
            await self.db.refresh(driver)
            return driver

        except IntegrityError as exc:
            await self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Phone number already exists",
            ) from exc

    async def get_drivers(self):
        return await self.driver_repository.get_all()

    async def get_driver(self, driver_id: int):
        driver = await self.driver_repository.get_by_id(driver_id)

        if driver is None:
            raise HTTPException(
                status_code=404,
                detail="Driver not found",
            )

        return driver

    async def get_driver_with_collection(self, driver_id: int):
        driver = await self.driver_repository.get_with_collections(
            driver_id
        )

        if driver is None:
            raise HTTPException(
                status_code=404,
                detail="Driver not found",
            )

        return driver

    async def get_driver_report(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        join_conditions = [
            Driver.id == TransportCollection.driver_id
        ]

        if start_date is not None:
            join_conditions.append(
                TransportCollection.collection_date >= start_date
            )

        if end_date is not None:
            join_conditions.append(
                TransportCollection.collection_date <= end_date
            )

        statement = (
            select(
                Driver.id.label("driver_id"),
                Driver.name.label("driver_name"),
                func.count(
                    TransportCollection.id
                ).label("total_records"),
                func.coalesce(
                    func.sum(TransportCollection.total_trips), 0
                ).label("total_trips"),
                func.coalesce(
                    func.sum(TransportCollection.total_collection), 0
                ).label("total_collection"),
                func.coalesce(
                    func.sum(TransportCollection.total_expense), 0
                ).label("total_expense"),
                func.coalesce(
                    func.sum(TransportCollection.net_collection), 0
                ).label("net_collection"),
                func.max(
                    TransportCollection.total_collection
                ).label("highest_collection"),
            )
            .outerjoin(
                TransportCollection,
                and_(*join_conditions),
            )
            .group_by(Driver.id, Driver.name)
            .order_by(Driver.id)
        )

        result = await self.db.execute(statement)

        return result.mappings().all()

