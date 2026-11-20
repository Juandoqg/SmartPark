from bson import ObjectId
from app.database.mongodb import MongoDB


class UserRepository:
    @staticmethod
    def collection():
        return MongoDB.get_database()["users"]

    @staticmethod
    def _serialize(user):
        if user is None:
            return None
        user["id"] = str(user.pop("_id"))
        return user

    @classmethod
    async def create(cls, data):
        result = await cls.collection().insert_one(data)
        return {"id": str(result.inserted_id), **data}

    @classmethod
    async def find_by_id(cls, user_id):
        return cls._serialize(await cls.collection().find_one({"_id": ObjectId(user_id)}))

    @classmethod
    async def find_by_email(cls, email):
        return cls._serialize(await cls.collection().find_one({"email": email}))

    @classmethod
    async def find_all(cls):
        users = []
        async for user in cls.collection().find({}).sort("created_at", -1):
            users.append(cls._serialize(user))
        return users

    @classmethod
    async def update(cls, user_id, data):
        await cls.collection().update_one({"_id": ObjectId(user_id)}, {"$set": data})
        return await cls.find_by_id(user_id)

    @classmethod
    async def delete(cls, user_id):
        result = await cls.collection().delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count == 1
