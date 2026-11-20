from datetime import datetime
import re
import unicodedata
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserFields(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    full_name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, min_length=7, max_length=20)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 3 or not any(char.isalpha() for char in value):
            raise ValueError("El nombre debe contener al menos 3 caracteres y letras")
        if any(unicodedata.category(char).startswith("C") for char in value):
            raise ValueError("El nombre contiene caracteres no permitidos")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not re.fullmatch(r"\+?[0-9][0-9 ()-]{5,18}[0-9]", value):
            raise ValueError("El teléfono solo puede contener dígitos, espacios, +, paréntesis y guiones")
        if not 7 <= len(re.sub(r"\D", "", value)) <= 15:
            raise ValueError("El teléfono debe contener entre 7 y 15 dígitos")
        return value


class UserCreate(UserFields):
    pass


class UserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    full_name: str | None = Field(default=None, min_length=3, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=7, max_length=20)

    @model_validator(mode="after")
    def validate_nonempty(self):
        if not self.model_fields_set:
            raise ValueError("Debe proporcionar al menos un campo para actualizar")
        if "full_name" in self.model_fields_set and self.full_name is None:
            raise ValueError("full_name no puede ser null")
        if "email" in self.model_fields_set and self.email is None:
            raise ValueError("email no puede ser null")
        return self

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value):
        if value is None:
            return value
        value = " ".join(value.split())
        if not any(char.isalpha() for char in value) or any(unicodedata.category(char).startswith("C") for char in value):
            raise ValueError("Nombre inválido")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return str(value).strip().lower() if value is not None else value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            return value
        value = value.strip()
        if not re.fullmatch(r"\+?[0-9][0-9 ()-]{5,18}[0-9]", value) or not 7 <= len(re.sub(r"\D", "", value)) <= 15:
            raise ValueError("Teléfono inválido: use entre 7 y 15 dígitos")
        return value


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone: str | None = None
    created_at: datetime
