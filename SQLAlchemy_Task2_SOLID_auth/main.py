
from fastapi import FastAPI

from app.api.routers.auth_router import router as auth_router
from app.api.routers.driver_router import router as driver_router
from app.api.routers.transport_collection_router import (
    router as collection_router,
)
from app.api.routers.report_router import router as report_router


app = FastAPI(
    title="Transport Collection System",
    description=(
        "Transport collection management with async SQLAlchemy, "
        "JWT authentication, and role-based authorization."
    ),
    version="1.0.0",
)



app.include_router(auth_router)
app.include_router(driver_router)
app.include_router(collection_router)
app.include_router(report_router)


@app.get("/")
async def home() -> dict[str, str]:
    return {"message": "Transport Collection System"}

