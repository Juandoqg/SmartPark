from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.schemas.parking_schema import ParkingCreate, ParkingUpdate
from app.services.parkingservice.parking_service_impl import ParkingNotFoundError, ParkingServiceImpl


def make_parking():
    return ParkingCreate(
        name="SmartPark Norte",
        address="Avenida 10 # 20-30",
        city="Cali",
        zones=[{"name": "Principal"}],
    )


@pytest.mark.asyncio
async def test_create_adds_timestamps_and_persists_data():
    repository = AsyncMock()
    repository.create.return_value = {"id": "abc", "name": "SmartPark Norte"}
    service = ParkingServiceImpl(parking_repository=repository)

    result = await service.create(make_parking())

    saved = repository.create.await_args.args[0]
    assert isinstance(saved["created_at"], datetime)
    assert isinstance(saved["updated_at"], datetime)
    assert saved["zones"] == [{"name": "Principal", "description": None}]
    assert result["id"] == "abc"


@pytest.mark.asyncio
async def test_find_all_delegates_to_repository():
    repository = AsyncMock()
    repository.find_all.return_value = [{"id": "abc"}]
    service = ParkingServiceImpl(parking_repository=repository)

    assert await service.find_all() == [{"id": "abc"}]


@pytest.mark.asyncio
async def test_find_by_id_raises_when_not_found():
    repository = AsyncMock()
    repository.find_by_id.return_value = None
    service = ParkingServiceImpl(parking_repository=repository)

    with pytest.raises(ParkingNotFoundError):
        await service.find_by_id("507f1f77bcf86cd799439011")


@pytest.mark.asyncio
async def test_update_requires_existing_parking_and_delegates_changes():
    repository = AsyncMock()
    repository.find_by_id.return_value = {"id": "abc", "city": "Cali"}
    repository.update.return_value = {"id": "abc", "city": "Bogota"}
    service = ParkingServiceImpl(parking_repository=repository)

    result = await service.update("abc", ParkingUpdate(city="Bogota"))

    changes = repository.update.await_args.args[1]
    assert changes["city"] == "Bogota"
    assert isinstance(changes["updated_at"], datetime)
    assert result["city"] == "Bogota"


@pytest.mark.asyncio
async def test_delete_requires_existing_parking():
    repository = AsyncMock()
    repository.find_by_id.return_value = {"id": "abc"}
    repository.delete.return_value = True
    service = ParkingServiceImpl(parking_repository=repository)

    assert await service.delete("abc") is True
    repository.delete.assert_awaited_once_with("abc")
