from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from app.repositories.user_repository import UserRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.vehicle_schema import VehicleCreate, VehicleUpdate
from app.services.vehicleservice.vehicle_service import VehicleService

class VehicleAlreadyExistsError(Exception): pass
class UserNotFoundError(Exception): pass
class VehicleNotFoundError(Exception): pass

class VehicleServiceImpl(VehicleService):
    async def _ensure_user(self, user_id):
        if not ObjectId.is_valid(user_id): raise UserNotFoundError("Identificador de usuario inválido")
        if await UserRepository.find_by_id(user_id) is None: raise UserNotFoundError("El usuario asociado no existe")

    async def create(self, vehicle: VehicleCreate):
        data = vehicle.model_dump()
        await self._ensure_user(data["user_id"])
        try: return await VehicleRepository.create(data)
        except DuplicateKeyError as exc: raise VehicleAlreadyExistsError("Ya existe un vehículo con esta placa") from exc

    async def find_all(self): return await VehicleRepository.find_all()
    async def find_by_user(self, user_id):
        await self._ensure_user(user_id)
        return await VehicleRepository.find_by_user(user_id)

    async def find_by_id(self, vehicle_id):
        if not ObjectId.is_valid(vehicle_id): raise VehicleNotFoundError("Identificador de vehículo inválido")
        vehicle = await VehicleRepository.find_by_id(vehicle_id)
        if vehicle is None: raise VehicleNotFoundError("Vehículo no encontrado")
        return vehicle

    async def update(self, vehicle_id, data: VehicleUpdate):
        await self.find_by_id(vehicle_id)
        changes = data.model_dump(exclude_unset=True)
        if "user_id" in changes: await self._ensure_user(changes["user_id"])
        try: return await VehicleRepository.update(vehicle_id, changes)
        except DuplicateKeyError as exc: raise VehicleAlreadyExistsError("Ya existe un vehículo con esta placa") from exc

    async def delete(self, vehicle_id):
        await self.find_by_id(vehicle_id)
        return await VehicleRepository.delete(vehicle_id)
