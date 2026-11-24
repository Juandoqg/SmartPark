from unittest.mock import AsyncMock
import pytest
from pymongo.errors import DuplicateKeyError
from app.schemas.vehicle_schema import VehicleCreate
from app.services.vehicleservice.vehicle_service_impl import (
    UserNotFoundError, VehicleAlreadyExistsError, VehicleServiceImpl,
)


def make_vehicle():
    return VehicleCreate(plate="abc123", vehicle_type="carro", user_id="507f1f77bcf86cd799439011")


@pytest.mark.asyncio
async def test_vehicle_requires_existing_user():
    user_repository = AsyncMock()
    user_repository.find_by_id.return_value = None
    vehicle_repository = AsyncMock()
    service = VehicleServiceImpl(user_repository=user_repository, vehicle_repository=vehicle_repository)
    with pytest.raises(UserNotFoundError):
        await service.create(make_vehicle())
    vehicle_repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_duplicate_plate_becomes_domain_error():
    user_repository = AsyncMock()
    user_repository.find_by_id.return_value = {"id": "507f1f77bcf86cd799439011"}
    vehicle_repository = AsyncMock()
    vehicle_repository.create.side_effect = DuplicateKeyError("duplicate")
    service = VehicleServiceImpl(user_repository=user_repository, vehicle_repository=vehicle_repository)
    with pytest.raises(VehicleAlreadyExistsError):
        await service.create(make_vehicle())
