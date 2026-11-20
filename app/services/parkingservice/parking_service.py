from abc import ABC, abstractmethod
from app.schemas.parking_schema import ParkingCreate, ParkingUpdate


class ParkingService(ABC):
    @abstractmethod
    async def create(self, parking: ParkingCreate): ...

    @abstractmethod
    async def find_all(self): ...

    @abstractmethod
    async def find_by_id(self, parking_id: str): ...

    @abstractmethod
    async def update(self, parking_id: str, data: ParkingUpdate): ...

    @abstractmethod
    async def delete(self, parking_id: str): ...
