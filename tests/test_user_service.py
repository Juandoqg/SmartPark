from datetime import datetime, timezone
from unittest.mock import AsyncMock
import pytest
from pymongo.errors import DuplicateKeyError
from app.schemas.user_schema import UserCreate
from app.services.userservice.user_service_impl import UserAlreadyExistsError, UserServiceImpl


@pytest.mark.asyncio
async def test_create_sets_utc_timestamp_and_normalized_email(monkeypatch):
    create = AsyncMock(return_value={"id": "1"})
    monkeypatch.setattr("app.services.userservice.user_service_impl.UserRepository.create", create)
    result = await UserServiceImpl().create(UserCreate(full_name="Ana Pérez", email="ANA@example.com", phone="3001234567", password="ClaveSegura123"))
    data = create.await_args.args[0]
    assert data["email"] == "ana@example.com"
    assert isinstance(data["created_at"], datetime)
    assert data["created_at"].tzinfo == timezone.utc
    assert data["password_hash"] != "ClaveSegura123"
    assert data["role"] == "user"
    assert result == {"id": "1"}


@pytest.mark.asyncio
async def test_duplicate_email_becomes_domain_error(monkeypatch):
    create = AsyncMock(side_effect=DuplicateKeyError("duplicate"))
    monkeypatch.setattr("app.services.userservice.user_service_impl.UserRepository.create", create)
    with pytest.raises(UserAlreadyExistsError):
        await UserServiceImpl().create(UserCreate(full_name="Ana Pérez", email="ana@example.com", phone="3001234567", password="ClaveSegura123"))
