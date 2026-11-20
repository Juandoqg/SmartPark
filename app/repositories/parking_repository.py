from bson import ObjectId
from app.database.mongodb import MongoDB


def _mongo_id(value: str):
    if not ObjectId.is_valid(value):
        raise ValueError("Identificador de sede inválido")
    return ObjectId(value)


class ParkingRepository:
    @staticmethod
    def collection():
        return MongoDB.get_database()["parkings"]

    @staticmethod
    def _serialize(parking):
        if parking is None:
            return None
        parking["id"] = str(parking.pop("_id"))
        return parking

    @classmethod
    async def create(cls, data: dict):
        result = await cls.collection().insert_one(data)
        return {"id": str(result.inserted_id), **data}

    @classmethod
    async def find_by_id(cls, parking_id: str):
        parking = await cls.collection().find_one({"_id": _mongo_id(parking_id)})
        return cls._serialize(parking)

    @classmethod
    async def find_all(cls):
        result = []
        async for parking in cls.collection().find({}).sort([("city", 1), ("name", 1)]):
            result.append(cls._serialize(parking))
        return result

    @classmethod
    async def update(cls, parking_id: str, data: dict):
        await cls.collection().update_one(
            {"_id": _mongo_id(parking_id)},
            {"$set": data},
        )
        return await cls.find_by_id(parking_id)

    @classmethod
    async def delete(cls, parking_id: str):
        result = await cls.collection().delete_one({"_id": _mongo_id(parking_id)})
        return result.deleted_count == 1
