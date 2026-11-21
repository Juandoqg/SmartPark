from uuid import uuid4

from app.database.postgres import PostgresDB, as_uuid, translate_constraint_errors


class PostgresParkingRepository:
    @staticmethod
    async def _get_zones(connection, parking_id):
        rows = await connection.fetch(
            "SELECT zone_id, name, level, description FROM parking_zones WHERE parking_id=$1 ORDER BY level, name",
            parking_id,
        )
        return [dict(row) for row in rows]

    @classmethod
    async def _get_one(cls, connection, parking_id):
        row = await connection.fetchrow(
            "SELECT id, name, address, city, created_at, updated_at FROM parkings WHERE id=$1",
            parking_id,
        )
        if row is None:
            return None
        result = {**dict(row), "id": str(row["id"])}
        result["zones"] = await cls._get_zones(connection, row["id"])
        return result

    @translate_constraint_errors
    async def create(self, data: dict):
        parking_id = uuid4()
        async with PostgresDB.get_pool().acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    "INSERT INTO parkings (id, name, address, city) VALUES ($1,$2,$3,$4)",
                    parking_id, data["name"], data["address"], data["city"],
                )
                for zone in data["zones"]:
                    await connection.execute(
                        "INSERT INTO parking_zones (parking_id, zone_id, name, level, description) "
                        "VALUES ($1,$2,$3,$4,$5)",
                        parking_id, zone["zone_id"], zone["name"], zone["level"], zone.get("description"),
                    )
                return await self._get_one(connection, parking_id)

    async def find_by_id(self, parking_id: str):
        async with PostgresDB.get_pool().acquire() as connection:
            return await self._get_one(connection, as_uuid(parking_id))

    async def find_all(self):
        async with PostgresDB.get_pool().acquire() as connection:
            rows = await connection.fetch(
                "SELECT id, name, address, city, created_at, updated_at FROM parkings ORDER BY city, name"
            )
            result = []
            for row in rows:
                item = {**dict(row), "id": str(row["id"])}
                item["zones"] = await self._get_zones(connection, row["id"])
                result.append(item)
            return result

    @translate_constraint_errors
    async def update(self, parking_id: str, data: dict):
        parking_uuid = as_uuid(parking_id)
        data = dict(data)
        data.pop("updated_at", None)  # PostgreSQL uses NOW() for this timestamp.
        allowed = {"name", "address", "city", "zones"}
        if not set(data) <= allowed:
            raise ValueError("Unsupported parking fields")
        async with PostgresDB.get_pool().acquire() as connection:
            async with connection.transaction():
                fields = {key: value for key, value in data.items() if key != "zones"}
                if fields:
                    assignments = ", ".join(
                        f"{field}=${index}" for index, field in enumerate(fields, start=2)
                    )
                    await connection.execute(
                        f"UPDATE parkings SET {assignments}, updated_at=NOW() WHERE id=$1",
                        parking_uuid, *fields.values(),
                    )
                elif "zones" in data:
                    await connection.execute(
                        "UPDATE parkings SET updated_at=NOW() WHERE id=$1", parking_uuid
                    )
                if "zones" in data:
                    await connection.execute("DELETE FROM parking_zones WHERE parking_id=$1", parking_uuid)
                    for zone in data["zones"]:
                        await connection.execute(
                            "INSERT INTO parking_zones (parking_id, zone_id, name, level, description) "
                            "VALUES ($1,$2,$3,$4,$5)",
                            parking_uuid, zone["zone_id"], zone["name"], zone["level"], zone.get("description"),
                        )
                return await self._get_one(connection, parking_uuid)

    async def delete(self, parking_id: str):
        async with PostgresDB.get_pool().acquire() as connection:
            status = await connection.execute("DELETE FROM parkings WHERE id=$1", as_uuid(parking_id))
        return status.endswith(" 1")
