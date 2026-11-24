from abc import ABC, abstractmethod


class ReportRepository(ABC):
    @abstractmethod
    async def occupancy_by_parking(self, parking_id=None): ...
    @abstractmethod
    async def revenue_by_parking(self, date_from, date_to, parking_id=None): ...
