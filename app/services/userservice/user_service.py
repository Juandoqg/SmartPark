from abc import ABC, abstractmethod
from app.schemas.user_schema import UserCreate


class UserService(ABC):

    @abstractmethod
    async def create(self, user: UserCreate):
        pass

    @abstractmethod
    async def find_all(self):
        pass