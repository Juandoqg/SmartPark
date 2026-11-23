from datetime import datetime, timezone
from app.services.tariffservice.tariff_service import TariffService
from app.services.tariffservice.tariff_errors import (
    TariffNotFoundError, TariffParkingNotFoundError, TariffValidationError,
)


class TariffServiceImpl(TariffService):
    def __init__(self, parking_repository, tariff_repository):
        self.parking_repository = parking_repository
        self.tariff_repository = tariff_repository

    async def create(self, parking_id, data):
        try:
            parking = await self.parking_repository.find_by_id(parking_id)
        except (ValueError, TypeError):
            parking = None
        if parking is None:
            raise TariffParkingNotFoundError("Sede no encontrada")
        if data.parking_id != parking_id:
            raise TariffValidationError("parking_id no coincide con la ruta")
        now = datetime.now(timezone.utc)
        values = data.model_dump()
        values.update(created_at=now, updated_at=now)
        return await self.tariff_repository.create(values)

    async def list_by_parking(self, parking_id, active=None):
        try:
            parking = await self.parking_repository.find_by_id(parking_id)
        except (ValueError, TypeError):
            parking = None
        if parking is None:
            raise TariffParkingNotFoundError("Sede no encontrada")
        return await self.tariff_repository.find_by_parking(parking_id, active)

    async def update(self, parking_id, tariff_id, data):
        try:
            current = await self.tariff_repository.find_by_id(tariff_id)
        except (ValueError, TypeError):
            current = None
        if current is None or current["parking_id"] != parking_id:
            raise TariffNotFoundError("Tarifa no encontrada")
        changes = data.model_dump(exclude_unset=True)
        changes["updated_at"] = datetime.now(timezone.utc)
        return await self.tariff_repository.update(tariff_id, changes)
