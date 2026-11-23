from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ParkingSessionEntry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    parking_id: str = Field(min_length=1, max_length=64)
    space_id: str = Field(min_length=1, max_length=64)
    vehicle_id: str = Field(min_length=1, max_length=64)
    tariff_id: str = Field(min_length=1, max_length=64)
    idempotency_key: str = Field(min_length=8, max_length=128)


class ParkingSessionResponse(BaseModel):
    id: str
    parking_id: str
    space_id: str
    user_id: str
    created_by: str
    vehicle_id: str
    tariff_id: str
    tariff_snapshot: dict
    entry_at: datetime
    exit_at: datetime | None = None
    duration_minutes: int | None = None
    total_amount: Decimal | None = None
    status: str
    payment_status: str
    created_at: datetime
    updated_at: datetime
