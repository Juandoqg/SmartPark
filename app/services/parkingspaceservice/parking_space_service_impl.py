from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError

from app.config.settings import settings
from app.repositories.ports import RepositoryConflictError
from app.schemas.parking_space_schema import ParkingSpaceCreate, ParkingSpaceUpdate
from app.services.parkingspaceservice.parking_space_service import ParkingSpaceService


class ParkingNotFoundError(Exception):
    pass


class ParkingSpaceNotFoundError(Exception):
    pass


class ParkingSpaceAlreadyExistsError(Exception):
    pass


class ParkingSpaceValidationError(Exception):
    pass


class ParkingSpaceServiceImpl(ParkingSpaceService):
    def __init__(self, parking_repository, space_repository, cache=None):
        self.parking_repository = parking_repository
        self.space_repository = space_repository
        self.cache = cache

    async def _parking(self, parking_id: str):
        try:
            parking = await self.parking_repository.find_by_id(parking_id)
        except (ValueError, TypeError):
            parking = None
        if parking is None:
            raise ParkingNotFoundError("Sede no encontrada")
        return parking

    async def _invalidate(self, parking_id: str):
        if self.cache:
            await self.cache.invalidate_parking_spaces(parking_id)

    async def create(self, parking_id: str, data: ParkingSpaceCreate):
        parking = await self._parking(parking_id)
        zones_by_id = {zone["zone_id"].casefold(): zone for zone in parking["zones"]}
        zone = zones_by_id.get(data.zone_id.casefold())
        if zone is None:
            raise ParkingSpaceValidationError("La zona indicada no pertenece a la sede")
        now = datetime.now(timezone.utc)
        values = data.model_dump()
        values.update({
            "parking_id": parking_id,
            "zone_id": zone["zone_id"],
            "zone_name": zone["name"],
            "created_at": now,
            "updated_at": now,
        })
        try:
            result = await self.space_repository.create(values)
        except (DuplicateKeyError, RepositoryConflictError) as exc:
            raise ParkingSpaceAlreadyExistsError("Ya existe un espacio con ese código en la sede") from exc
        await self._invalidate(parking_id)
        return result

    async def find_by_parking(self, parking_id: str, status: str | None = None, vehicle_type: str | None = None):
        await self._parking(parking_id)
        return await self.space_repository.find_by_parking(parking_id, status=status, vehicle_type=vehicle_type)

    async def availability(self, parking_id: str, vehicle_type: str | None = None):
        await self._parking(parking_id)
        key = f"smartpark:availability:{parking_id}:{vehicle_type or 'all'}"
        if self.cache:
            cached = await self.cache.get_json(key)
            if cached is not None:
                return cached
        spaces = await self.space_repository.find_by_parking(
            parking_id, status="available", vehicle_type=vehicle_type
        )
        result = {"parking_id": parking_id, "available_count": len(spaces), "spaces": spaces}
        if self.cache:
            await self.cache.set_json(key, result, ttl_seconds=settings.REDIS_AVAILABILITY_TTL_SECONDS)
        return result

    async def find_by_id(self, space_id: str):
        try:
            space = await self.space_repository.find_by_id(space_id)
        except (ValueError, TypeError):
            space = None
        if space is None:
            raise ParkingSpaceNotFoundError("Espacio no encontrado")
        return space

    async def update(self, space_id: str, data: ParkingSpaceUpdate):
        current = await self.find_by_id(space_id)
        changes = data.model_dump(exclude_unset=True)
        if "zone_id" in changes:
            parking = await self._parking(current["parking_id"])
            zones_by_id = {zone["zone_id"].casefold(): zone for zone in parking["zones"]}
            zone = zones_by_id.get(changes["zone_id"].casefold())
            if zone is None:
                raise ParkingSpaceValidationError("La zona indicada no pertenece a la sede")
            changes["zone_id"] = zone["zone_id"]
            changes["zone_name"] = zone["name"]
        changes["updated_at"] = datetime.now(timezone.utc)
        try:
            updated = await self.space_repository.update(space_id, changes)
        except (DuplicateKeyError, RepositoryConflictError) as exc:
            raise ParkingSpaceAlreadyExistsError("Ya existe un espacio con ese código en la sede") from exc
        await self._invalidate(current["parking_id"])
        return updated

    async def delete(self, space_id: str):
        current = await self.find_by_id(space_id)
        deleted = await self.space_repository.delete(space_id)
        await self._invalidate(current["parking_id"])
        return deleted
