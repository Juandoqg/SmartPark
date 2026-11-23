from abc import ABC, abstractmethod


class ReservationService(ABC):
    @abstractmethod
    async def create(self, data, user): ...

    @abstractmethod
    async def list_mine(self, user): ...

    @abstractmethod
    async def cancel(self, reservation_id: str, user): ...
