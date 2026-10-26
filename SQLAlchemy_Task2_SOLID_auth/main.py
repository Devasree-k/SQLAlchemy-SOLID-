# from fastapi import FastAPI

# from app.database.base import Base
# from app.database.connection import engine

# # # Import all models before creating tables.
# from app.models.driver_model import Driver
# from app.models.transport_collection_model import TransportCollection

# from app.routers.driver_router import router as driver_router
# from app.routers.transport_collection_router import router as collection_router

# from app.routers.report_router import router as report_router





# app = FastAPI(
#     title="Transport Collection System",
#     description="Transport collection management using async SQLAlchemy",
#     version="1.0.0",
# )


# app.include_router(driver_router)
# app.include_router(collection_router)
# app.include_router(report_router)


# @app.get("/")
# async def home():
#     return {
#         "message": "Transport Collection System"
#     }



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import CORS_ORIGINS
from app.routers.auth_router import router as auth_router
from app.routers.driver_router import router as driver_router
from app.routers.transport_collection_router import (
    router as collection_router,
)
from app.routers.report_router import router as report_router

from app.database.base import Base
from app.database.connection import engine

# Import every model so SQLAlchemy registers its table.
from app.models.driver_model import Driver
from app.models.transport_collection_model import TransportCollection
from app.models.user_model import User
from app.models.refresh_token_model import RefreshToken



from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(
    title="Transport Collection System",
    lifespan=lifespan,
)


# app = FastAPI(
#     title="Transport Collection System",
#     description=(
#         "Transport collection management with async SQLAlchemy, "
#         "JWT authentication, and role-based authorization."
#     ),
#     version="1.0.0",
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(driver_router)
app.include_router(collection_router)
app.include_router(report_router)


@app.get("/")
async def home() -> dict[str, str]:
    return {"message": "Transport Collection System"}