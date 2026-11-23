from pymongo.errors import DuplicateKeyError
from app.repositories.users.mongo_user_repository import MongoUserRepository
from app.repositories.vehicles.mongo_vehicle_repository import MongoVehicleRepository
from app.repositories.ports import RepositoryConflictError
from app.schemas.vehicle_schema import VehicleCreate, VehicleFields, VehicleUpdate
from app.services.vehicleservice.vehicle_service import VehicleService
from app.services.vehicleservice.vehicle_errors import (
    UserNotFoundError, VehicleAlreadyExistsError, VehicleNotFoundError, VehicleValidationError,
)

class VehicleServiceImpl(VehicleService):
    def __init__(self, user_repository=None, vehicle_repository=None):
        self.user_repository = user_repository or MongoUserRepository()
        self.vehicle_repository = vehicle_repository or MongoVehicleRepository()

    async def _ensure_user(self, user_id):
        try:
            user = await self.user_repository.find_by_id(user_id)
        except (ValueError, TypeError):
            user = None
        if user is None: raise UserNotFoundError("El usuario asociado no existe")

    async def create(self, vehicle: VehicleCreate):
        data = vehicle.model_dump()
        await self._ensure_user(data["user_id"])
        try: return await self.vehicle_repository.create(data)
        except (DuplicateKeyError, RepositoryConflictError) as exc: raise VehicleAlreadyExistsError("Ya existe un vehículo con esta placa") from exc

    async def find_all(self): return await self.vehicle_repository.find_all()
    async def find_by_user(self, user_id):
        await self._ensure_user(user_id)
        return await self.vehicle_repository.find_by_user(user_id)

    async def find_by_id(self, vehicle_id):
        try:
            vehicle = await self.vehicle_repository.find_by_id(vehicle_id)
        except (ValueError, TypeError):
            vehicle = None
        if vehicle is None: raise VehicleNotFoundError("Vehículo no encontrado")
        return vehicle

    async def update(self, vehicle_id, data: VehicleUpdate):
        current = await self.find_by_id(vehicle_id)
        changes = data.model_dump(exclude_unset=True)
        if "user_id" in changes: await self._ensure_user(changes["user_id"])
        final_values = {
            "plate": current.get("plate"),
            "vehicle_type": current["vehicle_type"],
            "user_id": current["user_id"],
            **changes,
        }
        try:
            VehicleFields.model_validate(final_values)
        except ValueError as exc:
            raise VehicleValidationError(str(exc)) from exc
        try: return await self.vehicle_repository.update(vehicle_id, changes)
        except (DuplicateKeyError, RepositoryConflictError) as exc: raise VehicleAlreadyExistsError("Ya existe un vehículo con esta placa") from exc

    async def delete(self, vehicle_id):
        await self.find_by_id(vehicle_id)
        return await self.vehicle_repository.delete(vehicle_id)
