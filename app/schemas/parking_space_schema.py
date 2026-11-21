from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator


SPACE_STATUSES = {"available", "occupied", "reserved", "out_of_service"}
VEHICLE_TYPES = {"carro", "moto", "bicicleta"}
VEHICLE_TYPE_ALIASES = {"car": "carro", "motorcycle": "moto", "bicycle": "bicicleta"}


def normalize_vehicle_type(value: str) -> str:
    value = value.strip().lower()
    value = VEHICLE_TYPE_ALIASES.get(value, value)
    if value not in VEHICLE_TYPES:
        raise ValueError(f"Tipos permitidos: {', '.join(sorted(VEHICLE_TYPES))}")
    return value


class ParkingSpaceFields(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    zone_id: str = Field(min_length=1, max_length=50)
    space_code: str = Field(min_length=1, max_length=30)
    allowed_vehicle_types: list[str] = Field(min_length=1, max_length=3)
    status: str = "available"

    @field_validator("zone_id", "space_code")
    @classmethod
    def normalize_text(cls, value: str, info: ValidationInfo) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("El campo no puede estar vacío")
        return value.upper() if info.field_name == "space_code" else value

    @field_validator("allowed_vehicle_types")
    @classmethod
    def validate_vehicle_types(cls, values: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(normalize_vehicle_type(value) for value in values))
        if not normalized:
            raise ValueError("Debe indicar al menos un tipo de vehículo")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in SPACE_STATUSES:
            raise ValueError(f"Estados permitidos: {', '.join(sorted(SPACE_STATUSES))}")
        return value


class ParkingSpaceCreate(ParkingSpaceFields):
    pass


class ParkingSpaceUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    zone_id: str | None = Field(default=None, min_length=1, max_length=50)
    space_code: str | None = Field(default=None, min_length=1, max_length=30)
    allowed_vehicle_types: list[str] | None = Field(default=None, min_length=1, max_length=3)
    status: str | None = None

    @model_validator(mode="after")
    def require_update_fields(self):
        if not self.model_fields_set:
            raise ValueError("Debe proporcionar al menos un campo para actualizar")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Los campos enviados no pueden ser null")
        return self

    @field_validator("zone_id", "space_code")
    @classmethod
    def normalize_text(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        value = " ".join(value.split())
        return value.upper() if info.field_name == "space_code" else value

    @field_validator("allowed_vehicle_types")
    @classmethod
    def validate_vehicle_types(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return values
        normalized = list(dict.fromkeys(normalize_vehicle_type(value) for value in values))
        if not normalized:
            raise ValueError("Debe indicar al menos un tipo de vehículo")
        return normalized

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().lower()
        if value not in SPACE_STATUSES:
            raise ValueError(f"Estados permitidos: {', '.join(sorted(SPACE_STATUSES))}")
        return value


class ParkingSpaceResponse(BaseModel):
    id: str
    parking_id: str
    zone_id: str
    zone_name: str
    space_code: str
    allowed_vehicle_types: list[str]
    status: str
    created_at: datetime
    updated_at: datetime
