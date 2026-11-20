import re
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PLATE_PATTERN = re.compile(r"^[A-Z0-9-]{5,10}$")
ALLOWED_TYPES = {"carro", "moto", "bicicleta"}
TYPES_REQUIRING_PLATE = {"carro", "moto"}

class VehicleFields(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    plate: str | None = Field(default=None, min_length=5, max_length=10)
    vehicle_type: str = Field(min_length=2, max_length=30)
    # Mongo ObjectId has 24 hex chars; PostgreSQL UUID has 36 chars with hyphens.
    # The validator below checks the exact format for either backend.
    user_id: str

    @field_validator("plate")
    @classmethod
    def normalize_plate(cls, value):
        if value is None:
            return value
        value = value.upper().replace(" ", "")
        if not PLATE_PATTERN.fullmatch(value): raise ValueError("Placa inválida: use 5–10 letras, números o guiones")
        return value

    @field_validator("vehicle_type")
    @classmethod
    def normalize_type(cls, value):
        value = value.lower()
        if value not in ALLOWED_TYPES: raise ValueError(f"Tipo permitido: {', '.join(sorted(ALLOWED_TYPES))}")
        return value

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value):
        if not re.fullmatch(r"(?:[0-9a-fA-F]{24}|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})", value):
            raise ValueError("user_id debe ser un ObjectId o UUID válido")
        return value.lower()

    @model_validator(mode="after")
    def require_plate_for_motor_vehicles(self):
        if self.vehicle_type in TYPES_REQUIRING_PLATE and not self.plate:
            raise ValueError("La placa es obligatoria para carros y motos")
        return self

class VehicleCreate(VehicleFields):
    pass

class VehicleUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    plate: str | None = Field(default=None, min_length=5, max_length=10)
    vehicle_type: str | None = Field(default=None, min_length=2, max_length=30)
    user_id: str | None = None

    @model_validator(mode="after")
    def validate_nonempty(self):
        if not self.model_fields_set: raise ValueError("Debe proporcionar al menos un campo para actualizar")
        for field in ("vehicle_type", "user_id"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} no puede ser null")
        return self

    @field_validator("plate")
    @classmethod
    def normalize_plate(cls, value):
        if value is None: return value
        value = value.upper().replace(" ", "")
        if not PLATE_PATTERN.fullmatch(value): raise ValueError("Placa inválida")
        return value

    @field_validator("vehicle_type")
    @classmethod
    def normalize_type(cls, value):
        if value is None: return value
        value = value.lower()
        if value not in ALLOWED_TYPES: raise ValueError("Tipo de vehículo inválido")
        return value

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value):
        if value is not None and not re.fullmatch(r"(?:[0-9a-fA-F]{24}|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})", value): raise ValueError("user_id debe ser un ObjectId o UUID válido")
        return value.lower() if value else value

class VehicleResponse(BaseModel):
    id: str
    plate: str | None = None
    vehicle_type: str
    user_id: str
