from pymongo import AsyncMongoClient
from app.config.settings import settings


class MongoDB:
    client = None
    database = None

    @classmethod
    async def connect(cls):
        cls.client = AsyncMongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
        await cls.client.admin.command("ping")
        cls.database = cls.client[settings.MONGODB_DATABASE]
        await cls.create_collections()
        print("MongoDB connected successfully")

    @classmethod
    async def create_collections(cls):
        existing = await cls.database.list_collection_names()
        for name in ("users", "vehicles"):
            if name not in existing:
                await cls.database.create_collection(name)
        await cls.database["users"].create_index("email", unique=True, name="unique_user_email")
        vehicle_indexes = await cls.database["vehicles"].index_information()
        existing_plate_index = vehicle_indexes.get("unique_vehicle_plate")
        expected_partial_filter = {"plate": {"$type": "string"}}
        if existing_plate_index and existing_plate_index.get("partialFilterExpression") != expected_partial_filter:
            await cls.database["vehicles"].drop_index("unique_vehicle_plate")
        await cls.database["vehicles"].create_index(
            "plate",
            unique=True,
            name="unique_vehicle_plate",
            partialFilterExpression=expected_partial_filter,
        )
        await cls.database["vehicles"].create_index("user_id", name="vehicles_by_user")

    @classmethod
    async def close(cls):
        if cls.client is not None:
            await cls.client.close()
            cls.client = None
            cls.database = None
            print("MongoDB connection closed")

    @classmethod
    def get_database(cls):
        if cls.database is None:
            raise RuntimeError("MongoDB is not connected")
        return cls.database
