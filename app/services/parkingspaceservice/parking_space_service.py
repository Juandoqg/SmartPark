from abc import ABC, abstractmethod


class ParkingSpaceService(ABC):
    @abstractmethod
    async def create(self, parking_id: str, data): ...

    @abstractmethod
    async def find_by_parking(self, parking_id: str, status: str | None = None, vehicle_type: str | None = None): ...

    @abstractmethod
    async def availability(self, parking_id: str, vehicle_type: str | None = None): ...

    @abstractmethod
    async def find_by_id(self, space_id: str): ...

    @abstractmethod
    async def update(self, space_id: str, data): ...

    @abstractmethod
    async def delete(self, space_id: str): ...
