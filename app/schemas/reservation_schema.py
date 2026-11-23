from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ReservationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    space_id: str = Field(min_length=1, max_length=64)
    vehicle_id: str = Field(min_length=1, max_length=64)
    tariff_id: str = Field(min_length=1, max_length=64)
    starts_at: datetime
    ends_at: datetime
    idempotency_key: str = Field(min_length=8, max_length=128)

    @field_validator("starts_at", "ends_at")
    @classmethod
    def require_timezone(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("La fecha debe incluir zona horaria")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_period(self):
        now = datetime.now(timezone.utc)
        if self.starts_at < now:
            raise ValueError("La reserva debe iniciar en el futuro")
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at debe ser posterior a starts_at")
        return self


class ReservationResponse(BaseModel):
    id: str
    parking_id: str
    space_id: str
    user_id: str
    vehicle_id: str
    tariff_id: str
    tariff_snapshot: dict
    estimated_total: Decimal
    starts_at: datetime
    ends_at: datetime
    status: str
    created_at: datetime
    updated_at: datetime
