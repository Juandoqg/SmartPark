from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):

    full_name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)


class UserResponse(BaseModel):

    id: str
    full_name: str
    email: EmailStr
    phone: str | None
    created_at: datetime