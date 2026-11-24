from abc import ABC, abstractmethod


class ReportService(ABC):
    @abstractmethod
    async def occupancy(self, parking_id=None): ...
    @abstractmethod
    async def revenue(self, date_from, date_to, parking_id=None): ...
