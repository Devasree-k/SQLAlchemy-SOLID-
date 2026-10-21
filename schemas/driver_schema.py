from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal

class DriverCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)

class DriverResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str | None


class DriverCollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_number: str
    total_collection: Decimal
    net_collection: Decimal


class DriverWithCollectionsResponse(DriverResponse):
    collections: list[DriverCollectionResponse]