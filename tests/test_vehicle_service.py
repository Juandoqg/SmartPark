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
async def test_vehicle_requires_existing_user(monkeypatch):
    find_one = AsyncMock(return_value=None)
    monkeypatch.setattr("app.services.vehicleservice.vehicle_service_impl.UserRepository.find_by_id", AsyncMock(return_value=None))
    with pytest.raises(UserNotFoundError):
        await VehicleServiceImpl().create(make_vehicle())


@pytest.mark.asyncio
async def test_duplicate_plate_becomes_domain_error(monkeypatch):
    monkeypatch.setattr("app.services.vehicleservice.vehicle_service_impl.UserRepository.find_by_id", AsyncMock(return_value={"id": "507f1f77bcf86cd799439011"}))
    create = AsyncMock(side_effect=DuplicateKeyError("duplicate"))
    monkeypatch.setattr("app.services.vehicleservice.vehicle_service_impl.VehicleRepository.create", create)
    with pytest.raises(VehicleAlreadyExistsError):
        await VehicleServiceImpl().create(make_vehicle())
