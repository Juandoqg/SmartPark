from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError
from app.repositories.user_repository import UserRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.repositories.ports import RepositoryConflictError
from app.schemas.user_schema import UserCreate, UserUpdate
from app.services.userservice.user_service import UserService


class UserAlreadyExistsError(Exception): pass
class UserNotFoundError(Exception): pass
class UserHasVehiclesError(Exception): pass


class UserServiceImpl(UserService):
    def __init__(self, user_repository=None, vehicle_repository=None):
        self.user_repository = user_repository or UserRepository()
        self.vehicle_repository = vehicle_repository or VehicleRepository()

    async def create(self, user: UserCreate):
        data = user.model_dump()
        data["email"] = str(data["email"]).lower()
        data["created_at"] = datetime.now(timezone.utc)
        try:
            return await self.user_repository.create(data)
        except (DuplicateKeyError, RepositoryConflictError) as exc:
            raise UserAlreadyExistsError("Ya existe un usuario con este correo") from exc

    async def find_all(self):
        return await self.user_repository.find_all()

    async def find_by_email(self, email: str):
        return await self.user_repository.find_by_email(email.strip().lower())

    async def find_by_id(self, user_id: str):
        try:
            user = await self.user_repository.find_by_id(user_id)
        except (ValueError, TypeError):
            user = None
        if user is None:
            raise UserNotFoundError("Usuario no encontrado")
        return user

    async def update(self, user_id: str, data: UserUpdate):
        await self.find_by_id(user_id)
        changes = data.model_dump(exclude_unset=True)
        if "email" in changes:
            changes["email"] = str(changes["email"]).lower()
        try:
            return await self.user_repository.update(user_id, changes)
        except (DuplicateKeyError, RepositoryConflictError) as exc:
            raise UserAlreadyExistsError("Ya existe un usuario con este correo") from exc

    async def delete(self, user_id: str):
        await self.find_by_id(user_id)
        linked_vehicles = await self.vehicle_repository.count_by_user(user_id)
        if linked_vehicles:
            raise UserHasVehiclesError("No se puede eliminar: el usuario todavía tiene vehículos asociados")
        try:
            return await self.user_repository.delete(user_id)
        except RepositoryConflictError as exc:
            raise UserHasVehiclesError("No se puede eliminar: el usuario todavía tiene vehículos asociados") from exc
