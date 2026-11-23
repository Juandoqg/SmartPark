from pymongo import AsyncMongoClient
from app.config.settings import settings


class MongoDB:
    client = None
    database = None

    @classmethod
    async def connect(cls):
        # BSON dates represent UTC instants; request aware datetimes when reading them.
        cls.client = AsyncMongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000, tz_aware=True)
        await cls.client.admin.command("ping")
        cls.database = cls.client[settings.MONGODB_DATABASE]
        await cls.create_collections()
        print("MongoDB connected successfully")

    @classmethod
    async def create_collections(cls):
        existing = await cls.database.list_collection_names()
        for name in ("users", "vehicles", "parkings", "parking_spaces", "tariffs", "reservations", "parking_sessions"):
            if name not in existing:
                await cls.database.create_collection(name)
        await cls.migrate_parking_zones()
        await cls.database["users"].update_many(
            {"role": {"$exists": False}}, {"$set": {"role": "user"}}
        )
        if settings.ADMIN_EMAIL.strip():
            await cls.database["users"].update_one(
                {"email": settings.ADMIN_EMAIL.strip().lower()}, {"$set": {"role": "admin"}}
            )
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
        await cls.database["parkings"].create_index([("city", 1), ("name", 1)], name="parkings_by_city_name")
        await cls.database["parking_spaces"].create_index(
            [("parking_id", 1), ("space_code", 1)], unique=True, name="unique_space_code_per_parking"
        )
        await cls.database["parking_spaces"].create_index(
            [("parking_id", 1), ("zone_id", 1), ("status", 1)], name="spaces_by_parking_zone_status"
        )
        await cls.database["tariffs"].create_index(
            [("parking_id", 1), ("vehicle_type", 1), ("active", 1)], name="tariffs_by_parking_vehicle_status"
        )
        await cls.database["reservations"].create_index(
            [("space_id", 1), ("starts_at", 1), ("ends_at", 1), ("status", 1)],
            name="reservations_by_space_time_status",
        )
        await cls.database["parking_sessions"].create_index(
            [("space_id", 1)], unique=True, partialFilterExpression={"status": "active"},
            name="one_active_session_per_space",
        )
        await cls.database["parking_sessions"].create_index(
            [("vehicle_id", 1)], unique=True, partialFilterExpression={"status": "active"},
            name="one_active_session_per_vehicle",
        )
        await cls.database["parking_sessions"].create_index(
            [("created_by", 1), ("idempotency_key", 1)], unique=True, name="unique_session_idempotency"
        )
        await cls.database["parking_sessions"].create_index(
            [("parking_id", 1), ("entry_at", -1)], name="sessions_by_parking_entry_date"
        )
        await cls.database["parking_sessions"].create_index(
            [("user_id", 1), ("entry_at", -1)], name="sessions_by_user_entry_date"
        )
        await cls.database["reservations"].create_index(
            [("user_id", 1), ("starts_at", -1)], name="reservations_by_user_date"
        )
        await cls.database["reservations"].create_index(
            [("user_id", 1), ("idempotency_key", 1)], unique=True, name="unique_reservation_idempotency"
        )

    @classmethod
    async def migrate_parking_zones(cls):
        """Give legacy embedded zones stable identifiers and levels."""
        async for parking in cls.database["parkings"].find({"zones": {"$exists": True}}):
            zones = parking.get("zones", [])
            migrated = []
            changed = False
            for zone in zones:
                zone = dict(zone)
                if not zone.get("zone_id"):
                    zone["zone_id"] = zone["name"]
                    changed = True
                if zone.get("level") is None:
                    zone["level"] = 1
                    changed = True
                migrated.append(zone)
            if changed:
                await cls.database["parkings"].update_one(
                    {"_id": parking["_id"]}, {"$set": {"zones": migrated}}
                )
        async for space in cls.database["parking_spaces"].find({"zone_id": {"$exists": False}}):
            parking = await cls.database["parkings"].find_one({"_id": space["parking_id"]})
            zone_name = space.get("zone_name", "")
            zone = next(
                (item for item in (parking or {}).get("zones", []) if item.get("name", "").casefold() == zone_name.casefold()),
                None,
            )
            if zone:
                await cls.database["parking_spaces"].update_one(
                    {"_id": space["_id"]}, {"$set": {"zone_id": zone["zone_id"]}}
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
