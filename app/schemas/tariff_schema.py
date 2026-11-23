from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TariffCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    parking_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=2, max_length=80)
    vehicle_type: str = Field(min_length=1, max_length=20)
    currency: str = Field(default="COP", min_length=3, max_length=3)
    hourly_rate: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    reservation_rate: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    billing_increment_minutes: int = Field(default=60, ge=1, le=1440)
    active: bool = True

    @field_validator("vehicle_type")
    @classmethod
    def normalize_vehicle_type(cls, value):
        value = value.strip().lower()
        aliases = {"car": "carro", "motorcycle": "moto", "bicycle": "bicicleta"}
        value = aliases.get(value, value)
        if value not in {"carro", "moto", "bicicleta"}:
            raise ValueError("Tipo de vehículo inválido")
        return value

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value):
        return value.upper()


class TariffUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str | None = Field(default=None, min_length=2, max_length=80)
    hourly_rate: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    reservation_rate: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    billing_increment_minutes: int | None = Field(default=None, ge=1, le=1440)
    active: bool | None = None

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("Debe proporcionar al menos un campo para actualizar")
        if any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError("Los campos enviados no pueden ser null")
        return self


class TariffResponse(BaseModel):
    id: str
    parking_id: str
    name: str
    vehicle_type: str
    currency: str
    hourly_rate: Decimal
    reservation_rate: Decimal
    billing_increment_minutes: int
    active: bool
    created_at: datetime
    updated_at: datetime
