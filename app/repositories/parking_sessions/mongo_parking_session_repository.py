from bson import ObjectId
from bson.decimal128 import Decimal128
from datetime import timezone
from pymongo.errors import DuplicateKeyError

from app.database.mongodb import MongoDB
from app.repositories.ports import RepositoryConflictError
from app.repositories.parking_sessions.parking_session_repository import ParkingSessionRepository


def _id(value):
    if not ObjectId.is_valid(value):
        raise ValueError("Identificador inválido")
    return ObjectId(value)


class MongoParkingSessionRepository(ParkingSessionRepository):
    @staticmethod
    def collection():
        return MongoDB.get_database()["parking_sessions"]

    @staticmethod
    def _serialize(item):
        if item is None:
            return None
        item["id"] = str(item.pop("_id"))
        for key in ("parking_id", "space_id", "user_id", "created_by", "vehicle_id", "tariff_id"):
            if isinstance(item.get(key), ObjectId):
                item[key] = str(item[key])
        if isinstance(item.get("total_amount"), Decimal128):
            item["total_amount"] = item["total_amount"].to_decimal()
        item["tariff_snapshot"] = {
            key: value.to_decimal() if isinstance(value, Decimal128) else value
            for key, value in item.get("tariff_snapshot", {}).items()
        }
        # Keep compatibility with records read by clients configured without tz_aware.
        for key in ("entry_at", "exit_at", "created_at", "updated_at"):
            value = item.get(key)
            if value is not None and value.tzinfo is None:
                item[key] = value.replace(tzinfo=timezone.utc)
        return item

    async def find_by_idempotency_key(self, user_id, key):
        item = await self.collection().find_one({"created_by": _id(user_id), "idempotency_key": key})
        return self._serialize(item)

    async def find_active_by_space(self, space_id):
        item = await self.collection().find_one({"space_id": _id(space_id), "status": "active"})
        return self._serialize(item)

    async def find_active_by_vehicle(self, vehicle_id):
        item = await self.collection().find_one({"vehicle_id": _id(vehicle_id), "status": "active"})
        return self._serialize(item)

    async def create_active(self, data):
        db = MongoDB.get_database()
        values = dict(data)
        for key in ("parking_id", "space_id", "user_id", "created_by", "vehicle_id", "tariff_id"):
            values[key] = _id(values[key])
        values["tariff_snapshot"] = {
            key: Decimal128(str(value)) if key in {"hourly_rate", "reservation_rate"} else value
            for key, value in values["tariff_snapshot"].items()
        }
        try:
            result = await self.collection().insert_one(values)
        except DuplicateKeyError as exc:
            raise RepositoryConflictError("Ya existe una sesión activa o la clave de idempotencia ya fue utilizada") from exc
        claimed = await db["parking_spaces"].update_one(
            {"_id": values["space_id"], "status": "available"},
            {"$set": {"status": "occupied", "active_session_id": result.inserted_id,
                      "updated_at": values["entry_at"]}},
        )
        if claimed.modified_count != 1:
            await self.collection().delete_one({"_id": result.inserted_id, "status": "active"})
            raise RepositoryConflictError("El espacio dejó de estar disponible")
        return self._serialize({"_id": result.inserted_id, **values})

    async def find_by_id(self, session_id):
        return self._serialize(await self.collection().find_one({"_id": _id(session_id)}))

    async def find(self, user_id=None, parking_id=None, status=None):
        query = {}
        if user_id:
            query["user_id"] = _id(user_id)
        if parking_id:
            query["parking_id"] = _id(parking_id)
        if status:
            query["status"] = status
        return [self._serialize(item) async for item in self.collection().find(query).sort("entry_at", -1)]

    async def close_active(self, session_id, exit_at, duration_minutes, total_amount):
        session_id = _id(session_id)
        current = await self.collection().find_one({"_id": session_id, "status": "active"})
        if current is None:
            return None
        result = await self.collection().update_one(
            {"_id": session_id, "status": "active"},
            {"$set": {"status": "completed", "exit_at": exit_at, "duration_minutes": duration_minutes,
                      "total_amount": Decimal128(str(total_amount)), "payment_status": "pending", "updated_at": exit_at}},
        )
        if result.modified_count != 1:
            return None
        await MongoDB.get_database()["parking_spaces"].update_one(
            {"_id": current["space_id"], "status": "occupied", "active_session_id": session_id},
            {"$set": {"status": "available", "updated_at": exit_at}, "$unset": {"active_session_id": ""}},
        )
        return await self.find_by_id(str(session_id))
