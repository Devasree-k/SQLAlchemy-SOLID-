from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.database import get_database
from repositories.driver_repository import DriverRepository
from repositories.transport_collection_repository import (
    TransportCollectionRepository,
)
from services.driver_service import DriverService
from services.transport_collection_service import (
    TransportCollectionService,
)


def get_driver_service(
    db: AsyncSession = Depends(get_database),
) -> DriverService:
    repository = DriverRepository(db)
    return DriverService(db, repository)


def get_collection_service(
    db: AsyncSession = Depends(get_database),
) -> TransportCollectionService:
    repository = TransportCollectionRepository(db)
    return TransportCollectionService(db, repository)