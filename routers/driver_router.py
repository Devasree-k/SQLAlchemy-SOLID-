from fastapi import APIRouter, Depends, status
from dependencies.database import get_database
from schemas.driver_schema import (
    DriverCreate,
    DriverResponse,
    DriverWithCollectionsResponse,
)
from services.driver_service import DriverService

from dependencies.service_dependencies import get_driver_service


router = APIRouter(
    prefix="/api/drivers",
    tags=["Drivers"],
)


@router.post(
    "/",
    response_model=DriverResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_driver(
    data: DriverCreate,
    service: DriverService = Depends(get_driver_service),
):
    return await service.create_driver(data)


@router.get("/", response_model=list[DriverResponse])
async def list_drivers(
    service: DriverService = Depends(get_driver_service),
):
    return await service.get_drivers()


@router.get(
    "/{driver_id}/collections",
    response_model=DriverWithCollectionsResponse,
)
async def read_driver_with_collections(
    driver_id: int,
    service: DriverService = Depends(get_driver_service),
):
    return await service.get_driver_with_collection(driver_id)


@router.get(
    "/{driver_id}",
    response_model=DriverResponse,
)
async def read_driver(
    driver_id: int,
    service: DriverService = Depends(get_driver_service),
):
    return await service.get_driver(driver_id)
