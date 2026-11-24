from datetime import datetime, timezone
from unittest.mock import AsyncMock
import pytest
from pymongo.errors import DuplicateKeyError
from app.schemas.user_schema import UserCreate
from app.services.userservice.user_service_impl import UserAlreadyExistsError, UserServiceImpl


@pytest.mark.asyncio
async def test_create_sets_utc_timestamp_and_normalized_email():
    user_repository = AsyncMock()
    user_repository.create.return_value = {"id": "1"}
    service = UserServiceImpl(user_repository=user_repository, vehicle_repository=AsyncMock())
    result = await service.create(UserCreate(full_name="Ana Pérez", email="ANA@example.com", phone="3001234567", password="ClaveSegura123"))
    data = user_repository.create.await_args.args[0]
    assert data["email"] == "ana@example.com"
    assert isinstance(data["created_at"], datetime)
    assert data["created_at"].tzinfo == timezone.utc
    assert data["password_hash"] != "ClaveSegura123"
    assert data["role"] == "user"
    assert result == {"id": "1"}


@pytest.mark.asyncio
async def test_duplicate_email_becomes_domain_error():
    user_repository = AsyncMock()
    user_repository.create.side_effect = DuplicateKeyError("duplicate")
    service = UserServiceImpl(user_repository=user_repository, vehicle_repository=AsyncMock())
    with pytest.raises(UserAlreadyExistsError):
        await service.create(UserCreate(full_name="Ana Pérez", email="ana@example.com", phone="3001234567", password="ClaveSegura123"))
