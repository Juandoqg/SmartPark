from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError

from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate


class UserAlreadyExistsError(Exception):
    pass


class UserService:

    @staticmethod
    async def create(user: UserCreate):

        user_data = user.model_dump()

        user_data["email"] = str(user_data["email"]).lower()
        user_data["created_at"] = datetime.now(timezone.utc)

        try:
            return await UserRepository.create(user_data)

        except DuplicateKeyError:
            raise UserAlreadyExistsError(
                "A user with this email already exists"
            )

    @staticmethod
    async def find_all():

        return await UserRepository.find_all()