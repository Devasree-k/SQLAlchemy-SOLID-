
from datetime import date

import pytest

from app.models.driver_model import Driver
from app.repositories.implementations.driver_repository import (
    DriverRepository,
)


@pytest.mark.asyncio
async def test_create_and_get_driver(db_session):
    # Arrange: create the repository and driver.
    repository = DriverRepository(db_session)

    driver = Driver(
        name="Arun",
        phone="9876543210",
        joined_date=date(2025, 1, 10),
        license_number="TN123456",
    )

    # Act: save and retrieve the driver.
    await repository.create(driver)
    await db_session.commit()

    result = await repository.get_by_id(driver.id)

    # Assert: check the saved database record.
    assert result is not None
    assert result.name == "Arun"
    assert result.phone == "9876543210"
    assert result.license_number == "TN123456"
