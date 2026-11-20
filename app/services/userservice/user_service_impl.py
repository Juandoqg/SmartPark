from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate
from app.services.userservice.user_service import UserService


class UserAlreadyExistsError(Exception): pass
class UserNotFoundError(Exception): pass
class UserHasVehiclesError(Exception): pass


class UserServiceImpl(UserService):
    async def create(self, user: UserCreate):
        data = user.model_dump()
        data["email"] = str(data["email"]).lower()
        data["created_at"] = datetime.now(timezone.utc)
        try:
            return await UserRepository.create(data)
        except DuplicateKeyError as exc:
            raise UserAlreadyExistsError("Ya existe un usuario con este correo") from exc

    async def find_all(self):
        return await UserRepository.find_all()

    async def find_by_email(self, email: str):
        return await UserRepository.find_by_email(email.strip().lower())

    async def find_by_id(self, user_id: str):
        if not ObjectId.is_valid(user_id):
            raise UserNotFoundError("Identificador de usuario inválido")
        user = await UserRepository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError("Usuario no encontrado")
        return user

    async def update(self, user_id: str, data: UserUpdate):
        await self.find_by_id(user_id)
        changes = data.model_dump(exclude_unset=True)
        if "email" in changes:
            changes["email"] = str(changes["email"]).lower()
        try:
            return await UserRepository.update(user_id, changes)
        except DuplicateKeyError as exc:
            raise UserAlreadyExistsError("Ya existe un usuario con este correo") from exc

    async def delete(self, user_id: str):
        await self.find_by_id(user_id)
        db = UserRepository.collection().database
        linked_vehicles = await db["vehicles"].count_documents({"user_id": ObjectId(user_id)})
        if linked_vehicles:
            raise UserHasVehiclesError("No se puede eliminar: el usuario todavía tiene vehículos asociados")
        return await UserRepository.delete(user_id)
