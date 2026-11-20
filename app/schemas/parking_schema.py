from datetime import datetime
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ParkingZone(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=150)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not any(char.isalpha() for char in value):
            raise ValueError("El nombre de la zona debe contener letras")
        if any(unicodedata.category(char).startswith("C") for char in value):
            raise ValueError("El nombre de la zona contiene caracteres no permitidos")
        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.split())
        return value or None


class ParkingFields(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=3, max_length=100)
    address: str = Field(min_length=5, max_length=200)
    city: str = Field(min_length=2, max_length=80)
    zones: list[ParkingZone] = Field(min_length=1, max_length=50)

    @field_validator("name", "address")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        value = " ".join(value.split())
        if not any(char.isalpha() for char in value):
            raise ValueError("El campo debe contener letras")
        if any(unicodedata.category(char).startswith("C") for char in value):
            raise ValueError("El campo contiene caracteres no permitidos")
        return value

    @field_validator("city")
    @classmethod
    def normalize_city(cls, value: str) -> str:
        value = " ".join(value.split())
        if not any(char.isalpha() for char in value):
            raise ValueError("La ciudad debe contener letras")
        if any(unicodedata.category(char).startswith("C") for char in value):
            raise ValueError("La ciudad contiene caracteres no permitidos")
        return value.title()

    @field_validator("zones")
    @classmethod
    def validate_unique_zones(cls, zones: list[ParkingZone]) -> list[ParkingZone]:
        normalized_names = [zone.name.casefold() for zone in zones]
        if len(normalized_names) != len(set(normalized_names)):
            raise ValueError("No puede haber zonas con nombres duplicados dentro de una sede")
        return zones


class ParkingCreate(ParkingFields):
    pass


class ParkingUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str | None = Field(default=None, min_length=3, max_length=100)
    address: str | None = Field(default=None, min_length=5, max_length=200)
    city: str | None = Field(default=None, min_length=2, max_length=80)
    zones: list[ParkingZone] | None = Field(default=None, min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("Debe proporcionar al menos un campo para actualizar")
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} no puede ser null")
        return self

    @field_validator("name", "address")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.split())
        if not any(char.isalpha() for char in value):
            raise ValueError("El campo debe contener letras")
        if any(unicodedata.category(char).startswith("C") for char in value):
            raise ValueError("El campo contiene caracteres no permitidos")
        return value

    @field_validator("city")
    @classmethod
    def normalize_city(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.split())
        if not any(char.isalpha() for char in value):
            raise ValueError("La ciudad debe contener letras")
        if any(unicodedata.category(char).startswith("C") for char in value):
            raise ValueError("La ciudad contiene caracteres no permitidos")
        return value.title()

    @field_validator("zones")
    @classmethod
    def validate_unique_zones(cls, zones: list[ParkingZone] | None) -> list[ParkingZone] | None:
        if zones is None:
            return None
        normalized_names = [zone.name.casefold() for zone in zones]
        if len(normalized_names) != len(set(normalized_names)):
            raise ValueError("No puede haber zonas con nombres duplicados dentro de una sede")
        return zones


class ParkingResponse(BaseModel):
    id: str
    name: str
    address: str
    city: str
    zones: list[ParkingZone]
    created_at: datetime
    updated_at: datetime
