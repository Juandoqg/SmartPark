from bson import ObjectId

from app.database.mongodb import MongoDB
from app.repositories.parking_spaces.parking_space_repository import ParkingSpaceRepository


def _mongo_id(value: str):
    if not ObjectId.is_valid(value):
        raise ValueError("Identificador inválido")
    return ObjectId(value)


class MongoParkingSpaceRepository(ParkingSpaceRepository):
    @staticmethod
    def collection():
        return MongoDB.get_database()["parking_spaces"]

    @staticmethod
    def _serialize(space):
        if space is None:
            return None
        space["id"] = str(space.pop("_id"))
        space["parking_id"] = str(space["parking_id"])
        return space

    @classmethod
    async def create(cls, data: dict):
        data = {**data, "parking_id": _mongo_id(data["parking_id"])}
        result = await cls.collection().insert_one(data)
        return {"id": str(result.inserted_id), **{**data, "parking_id": str(data["parking_id"])} }

    @classmethod
    async def find_by_id(cls, space_id: str):
        return cls._serialize(await cls.collection().find_one({"_id": _mongo_id(space_id)}))

    @classmethod
    async def find_by_parking(cls, parking_id: str, status: str | None = None, vehicle_type: str | None = None):
        query = {"parking_id": _mongo_id(parking_id)}
        if status:
            query["status"] = status
        if vehicle_type:
            query["allowed_vehicle_types"] = vehicle_type
        cursor = cls.collection().find(query).sort("space_code", 1)
        return [cls._serialize(space) async for space in cursor]

    @classmethod
    async def update(cls, space_id: str, data: dict):
        await cls.collection().update_one({"_id": _mongo_id(space_id)}, {"$set": data})
        return await cls.find_by_id(space_id)

    @classmethod
    async def delete(cls, space_id: str):
        result = await cls.collection().delete_one({"_id": _mongo_id(space_id)})
        return result.deleted_count == 1
