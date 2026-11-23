from abc import ABC, abstractmethod


class TariffRepository(ABC):
    @abstractmethod
    async def create(self, data: dict): ...

    @abstractmethod
    async def find_by_id(self, tariff_id: str): ...

    @abstractmethod
    async def find_by_parking(self, parking_id: str, active: bool | None = None): ...

    @abstractmethod
    async def update(self, tariff_id: str, data: dict): ...
