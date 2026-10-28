# python -m pip install pytest pytest-asyncio httpx aiosqlite



import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from app.database.base import Base
from app.models.driver_model import Driver
from app.models.transport_collection_model import TransportCollection


@pytest_asyncio.fixture
async def db_session():
    # Use an isolated in-memory database.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:"
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    async with SessionLocal() as session:
        yield session

    await engine.dispose()
