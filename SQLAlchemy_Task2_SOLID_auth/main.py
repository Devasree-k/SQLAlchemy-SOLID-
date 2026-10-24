from fastapi import FastAPI

from app.database.base import Base
from app.database.connection import engine

# # Import all models before creating tables.
from app.models.driver_model import Driver
from app.models.transport_collection_model import TransportCollection

from app.routers.driver_router import router as driver_router
from app.routers.transport_collection_router import router as collection_router

from app.routers.report_router import router as report_router





app = FastAPI(
    title="Transport Collection System",
    description="Transport collection management using async SQLAlchemy",
    version="1.0.0",
)


app.include_router(driver_router)
app.include_router(collection_router)
app.include_router(report_router)


@app.get("/")
async def home():
    return {
        "message": "Transport Collection System"
    }
