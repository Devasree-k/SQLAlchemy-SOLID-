
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from main import app
from app.api.dependencies.auth_dependencies import get_current_user
from app.api.dependencies.service_dependencies import get_driver_service


@pytest.fixture
def client():
    # Simulate a logged-in admin user.
    async def fake_current_user():
        return SimpleNamespace(
            id=1,
            role="admin",
            is_active=True,
        )

    app.dependency_overrides[get_current_user] = (
        fake_current_user
    )

    yield TestClient(app)

    # Remove overrides after each test.
    app.dependency_overrides.clear()


def test_list_drivers_api(client):
    # Arrange: prepare a fake service response.
    driver = SimpleNamespace(
        id=1,
        name="Arun",
        phone="9876543210",
        dob=None,
        joined_date=date(2025, 1, 10),
        license_number="TN123456",
    )

    service = AsyncMock()
    service.get_drivers.return_value = [driver]

    app.dependency_overrides[get_driver_service] = (
        lambda: service
    )

    # Act: send an HTTP request.
    response = client.get("/api/drivers/")

    # Assert: check the API response.
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Arun"


def test_create_driver_forbidden_for_driver_role(client):
    # Arrange: simulate a user with the driver role.
    async def fake_driver_user():
        return SimpleNamespace(
            id=2,
            role="driver",
            is_active=True,
        )

    app.dependency_overrides[get_current_user] = (
        fake_driver_user
    )

    # Act: attempt an admin-only operation.
    response = client.post(
        "/api/drivers/",
        json={
            "name": "Arun",
            "phone": "9876543210",
            "dob": None,
            "joined_date": "2025-01-10",
            "license_number": "TN123456",
        },
    )

    # Assert: the driver role must be rejected.
    assert response.status_code == 403
