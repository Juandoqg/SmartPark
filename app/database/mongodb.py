from pymongo import AsyncMongoClient

from app.config.settings import settings


class MongoDB:

    client = None
    database = None

    @classmethod
    async def connect(cls):

        cls.client = AsyncMongoClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000
        )

        await cls.client.admin.command("ping")

        cls.database = cls.client[settings.MONGODB_DATABASE]

        await cls.create_collections()

        print("MongoDB connected successfully")

    @classmethod
    async def create_collections(cls):

        existing_collections = await cls.database.list_collection_names()

        if "users" not in existing_collections:
            await cls.database.create_collection("users")

        await cls.database["users"].create_index(
            "email",
            unique=True,
            name="unique_user_email"
        )

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