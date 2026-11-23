from datetime import datetime, timezone
from bson import ObjectId
from bson.decimal128 import Decimal128
from app.database.mongodb import MongoDB
from app.repositories.reservations.reservation_repository import ReservationRepository


def _id(value):
    if not ObjectId.is_valid(value):
        raise ValueError("Identificador inválido")
    return ObjectId(value)


class MongoReservationRepository(ReservationRepository):
    @staticmethod
    def collection():
        return MongoDB.get_database()["reservations"]

    @staticmethod
    def serialize(item):
        if item is None:
            return None
        item["id"] = str(item.pop("_id"))
        for key in ("parking_id", "space_id", "user_id", "vehicle_id", "tariff_id"):
            if isinstance(item.get(key), ObjectId):
                item[key] = str(item[key])
        if isinstance(item.get("estimated_total"), Decimal128):
            item["estimated_total"] = item["estimated_total"].to_decimal()
        for key, value in item.get("tariff_snapshot", {}).items():
            if isinstance(value, Decimal128):
                item["tariff_snapshot"][key] = value.to_decimal()
        return item

    async def find_by_idempotency_key(self, user_id, key):
        return self.serialize(await self.collection().find_one({"user_id": _id(user_id), "idempotency_key": key}))

    async def has_overlap(self, space_id, starts_at, ends_at):
        return await self.collection().find_one({"space_id": _id(space_id), "status": "confirmed",
            "starts_at": {"$lt": ends_at}, "ends_at": {"$gt": starts_at}}, {"_id": 1}) is not None

    async def create(self, data):
        values = dict(data)
        for key in ("parking_id", "space_id", "user_id", "vehicle_id", "tariff_id"):
            values[key] = _id(values[key])
        values["estimated_total"] = Decimal128(str(values["estimated_total"]))
        values["tariff_snapshot"] = {key: Decimal128(str(value)) if key in {"hourly_rate", "reservation_rate"} else value
                                      for key, value in values["tariff_snapshot"].items()}
        result = await self.collection().insert_one(values)
        return self.serialize({"_id": result.inserted_id, **values})

    async def find_by_user(self, user_id):
        return [self.serialize(x) async for x in self.collection().find({"user_id": _id(user_id)}).sort("starts_at", -1)]

    async def cancel(self, reservation_id, user_id):
        await self.collection().update_one({"_id": _id(reservation_id), "user_id": _id(user_id), "status": "confirmed"},
            {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc)}})
        item = await self.collection().find_one({"_id": _id(reservation_id), "user_id": _id(user_id), "status": "cancelled"})
        return self.serialize(item)
