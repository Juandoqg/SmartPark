from bson import ObjectId
from app.database.mongodb import MongoDB

class VehicleRepository:
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
        data = {**data, "user_id": ObjectId(data["user_id"])}
        result = await cls.collection().insert_one(data)
        return {"id": str(result.inserted_id), **{**data, "user_id": str(data["user_id"])}}

    @classmethod
    async def find_by_id(cls, vehicle_id):
        return cls._serialize(await cls.collection().find_one({"_id": ObjectId(vehicle_id)}))

    @classmethod
    async def find_by_plate(cls, plate):
        return cls._serialize(await cls.collection().find_one({"plate": plate}))

    @classmethod
    async def find_by_user(cls, user_id):
        result = []
        async for vehicle in cls.collection().find({"user_id": ObjectId(user_id)}).sort("plate", 1):
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
        if "user_id" in changes: changes["user_id"] = ObjectId(changes["user_id"])
        await cls.collection().update_one({"_id": ObjectId(vehicle_id)}, {"$set": changes})
        return await cls.find_by_id(vehicle_id)

    @classmethod
    async def delete(cls, vehicle_id):
        result = await cls.collection().delete_one({"_id": ObjectId(vehicle_id)})
        return result.deleted_count == 1
