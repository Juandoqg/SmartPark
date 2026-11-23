from abc import ABC, abstractmethod


class ReservationRepository(ABC):
    @abstractmethod
    async def create(self, data: dict): ...

    @abstractmethod
    async def find_by_idempotency_key(self, user_id: str, key: str): ...

    @abstractmethod
    async def has_overlap(self, space_id: str, starts_at, ends_at): ...

    @abstractmethod
    async def find_by_user(self, user_id: str): ...

    @abstractmethod
    async def cancel(self, reservation_id: str, user_id: str): ...
