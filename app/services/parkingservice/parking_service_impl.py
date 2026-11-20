from datetime import datetime, timezone

from app.repositories.parking_repository import ParkingRepository
from app.schemas.parking_schema import ParkingCreate, ParkingUpdate
from app.services.parkingservice.parking_service import ParkingService


class ParkingNotFoundError(Exception):
    pass


class ParkingServiceImpl(ParkingService):
    def __init__(self, parking_repository=None):
        self.parking_repository = parking_repository or ParkingRepository()

    async def create(self, parking: ParkingCreate):
        now = datetime.now(timezone.utc)
        data = parking.model_dump()
        data["created_at"] = now
        data["updated_at"] = now
        return await self.parking_repository.create(data)

    async def find_all(self):
        return await self.parking_repository.find_all()

    async def find_by_id(self, parking_id: str):
        try:
            parking = await self.parking_repository.find_by_id(parking_id)
        except (ValueError, TypeError):
            parking = None
        if parking is None:
            raise ParkingNotFoundError("Sede no encontrada")
        return parking

    async def update(self, parking_id: str, data: ParkingUpdate):
        await self.find_by_id(parking_id)
        changes = data.model_dump(exclude_unset=True)
        changes["updated_at"] = datetime.now(timezone.utc)
        return await self.parking_repository.update(parking_id, changes)

    async def delete(self, parking_id: str):
        await self.find_by_id(parking_id)
        return await self.parking_repository.delete(parking_id)
