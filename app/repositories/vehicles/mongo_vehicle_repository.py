from bson import ObjectId
from uuid import UUID
from app.database.mongodb import MongoDB
from app.repositories.vehicles.vehicle_repository import VehicleRepository


def _mongo_id(value):
    if ObjectId.is_valid(value):
        return ObjectId(value)
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Identificador inválido")

class MongoVehicleRepository(VehicleRepository):
    @staticmethod
    def collection(): return MongoDB.get_database()["vehicles"]

    @staticmethod
    def _serialize(vehicle):
        if vehicle is None: return None
        vehicle["id"] = str(vehicle.pop("_id"))
        vehicle["user_id"] = str(vehicle["user_id"])
        return vehicle

    @classmethod
    async def create(cls, data):
        data = {**data, "user_id": _mongo_id(data["user_id"])}
        result = await cls.collection().insert_one(data)
        return {"id": str(result.inserted_id), **{**data, "user_id": str(data["user_id"])}}

    @classmethod
    async def find_by_id(cls, vehicle_id):
        return cls._serialize(await cls.collection().find_one({"_id": _mongo_id(vehicle_id)}))

    @classmethod
    async def find_by_plate(cls, plate):
        return cls._serialize(await cls.collection().find_one({"plate": plate}))

    @classmethod
    async def find_by_user(cls, user_id):
        result = []
        async for vehicle in cls.collection().find({"user_id": _mongo_id(user_id)}).sort("plate", 1):
            result.append(cls._serialize(vehicle))
        return result

    @classmethod
    async def find_all(cls):
        result = []
        async for vehicle in cls.collection().find({}).sort("plate", 1):
            result.append(cls._serialize(vehicle))
        return result

    @classmethod
    async def update(cls, vehicle_id, data):
        changes = dict(data)
        if "user_id" in changes: changes["user_id"] = _mongo_id(changes["user_id"])
        await cls.collection().update_one({"_id": _mongo_id(vehicle_id)}, {"$set": changes})
        return await cls.find_by_id(vehicle_id)

    @classmethod
    async def delete(cls, vehicle_id):
        result = await cls.collection().delete_one({"_id": _mongo_id(vehicle_id)})
        return result.deleted_count == 1

    @classmethod
    async def count_by_user(cls, user_id):
        return await cls.collection().count_documents({"user_id": _mongo_id(user_id)})
