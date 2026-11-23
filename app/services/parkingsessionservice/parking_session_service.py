from abc import ABC, abstractmethod


class ParkingSessionService(ABC):
    @abstractmethod
    async def entry(self, data, user): ...
    @abstractmethod
    async def exit(self, session_id, user): ...
    @abstractmethod
    async def list_sessions(self, user, parking_id=None, status=None): ...
