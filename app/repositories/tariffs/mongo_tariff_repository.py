from bson import ObjectId
from bson.decimal128 import Decimal128
from decimal import Decimal
from app.database.mongodb import MongoDB
from app.repositories.tariffs.tariff_repository import TariffRepository


def _id(value):
    if not ObjectId.is_valid(value):
        raise ValueError("Identificador inválido")
    return ObjectId(value)


class MongoTariffRepository(TariffRepository):
    @staticmethod
    def collection():
        return MongoDB.get_database()["tariffs"]

    @staticmethod
    def serialize(item):
        if item is None:
            return None
        item["id"] = str(item.pop("_id"))
        if isinstance(item.get("parking_id"), ObjectId):
            item["parking_id"] = str(item["parking_id"])
        for key in ("hourly_rate", "reservation_rate"):
            if isinstance(item.get(key), Decimal128):
                item[key] = item[key].to_decimal()
        return item

    async def create(self, data):
        data = {**data, "parking_id": _id(data["parking_id"]),
                "hourly_rate": Decimal128(str(data["hourly_rate"])),
                "reservation_rate": Decimal128(str(data["reservation_rate"]))}
        result = await self.collection().insert_one(data)
        return self.serialize({"_id": result.inserted_id, **data})

    async def find_by_id(self, tariff_id):
        return self.serialize(await self.collection().find_one({"_id": _id(tariff_id)}))

    async def find_by_parking(self, parking_id, active=None):
        query = {"parking_id": _id(parking_id)}
        if active is not None:
            query["active"] = active
        return [self.serialize(x) async for x in self.collection().find(query).sort("name", 1)]

    async def update(self, tariff_id, data):
        data = dict(data)
        for key in ("hourly_rate", "reservation_rate"):
            if key in data:
                data[key] = Decimal128(str(data[key]))
        await self.collection().update_one({"_id": _id(tariff_id)}, {"$set": data})
        return await self.find_by_id(tariff_id)
