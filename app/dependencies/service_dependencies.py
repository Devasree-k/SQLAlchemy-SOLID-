from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_database
from app.repositories.implementations.driver_repository import DriverRepository
from app.repositories.implementations.transport_collection_repository import (
    TransportCollectionRepository,
)
from app.services.driver_service import DriverService
from app.services.transport_collection_service import (
    TransportCollectionService,
)

# Dependency function for driver service 
def get_driver_service(
    db: AsyncSession = Depends(get_database),
) -> DriverService:
    repository = DriverRepository(db)
    return DriverService(db, repository)

#Dependency function for transport_collection_service
def get_collection_service(
    db: AsyncSession = Depends(get_database),
) -> TransportCollectionService:
    repository = TransportCollectionRepository(db)
    return TransportCollectionService(db, repository)