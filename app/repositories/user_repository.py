from app.database.mongodb import MongoDB


class UserRepository:

    @staticmethod
    def collection():
        return MongoDB.get_database()["users"]

    @classmethod
    async def create(cls, user_data: dict):

        result = await cls.collection().insert_one(user_data)

        return {
            "id": str(result.inserted_id),
            **user_data
        }

    @classmethod
    async def find_by_email(cls, email: str):

        user = await cls.collection().find_one({
            "email": email
        })

        if user is None:
            return None

        user["id"] = str(user.pop("_id"))

        return user

    @classmethod
    async def find_all(cls):

        cursor = cls.collection().find({})

        users = []

        async for user in cursor:
            user["id"] = str(user.pop("_id"))
            users.append(user)

        return users