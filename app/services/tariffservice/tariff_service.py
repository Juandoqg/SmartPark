from abc import ABC, abstractmethod


class TariffService(ABC):
    @abstractmethod
    async def create(self, parking_id: str, data): ...

    @abstractmethod
    async def list_by_parking(self, parking_id: str, active=None): ...

    @abstractmethod
    async def update(self, parking_id: str, tariff_id: str, data): ...
