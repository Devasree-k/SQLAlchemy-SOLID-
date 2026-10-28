
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.services.driver_service import DriverService


@pytest.mark.asyncio
async def test_get_driver_success():
    # Arrange: prepare a fake driver and repository.
    driver = SimpleNamespace(id=1, name="Arun")

    repository = AsyncMock()
    repository.get_by_id.return_value = driver

    service = DriverService(
        db=AsyncMock(),
        driver_repository=repository,
    )

    # Act: call the service method.
    result = await service.get_driver(1)

    # Assert: verify the returned driver.
    assert result.id == 1
    assert result.name == "Arun"
    repository.get_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_driver_not_found():
    # Arrange: simulate a missing driver.
    repository = AsyncMock()
    repository.get_by_id.return_value = None

    service = DriverService(
        db=AsyncMock(),
        driver_repository=repository,
    )

    # Act and assert: expect a 404 error.
    with pytest.raises(HTTPException) as error:
        await service.get_driver(100)

    assert error.value.status_code == 404
    assert error.value.detail == "Driver not found"
