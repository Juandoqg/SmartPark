from uuid import uuid4

from app.database.postgres import PostgresDB, as_uuid, translate_constraint_errors
from app.repositories.parking_spaces.parking_space_repository import ParkingSpaceRepository


def _serialize(row):
    if row is None:
        return None
    result = dict(row)
    result["id"] = str(result.pop("id"))
    result["parking_id"] = str(result["parking_id"])
    return result


class PostgresParkingSpaceRepository(ParkingSpaceRepository):
    @translate_constraint_errors
    async def create(self, data: dict):
        async with PostgresDB.get_pool().acquire() as connection:
            row = await connection.fetchrow(
                "INSERT INTO parking_spaces (id, parking_id, zone_id, zone_name, space_code, allowed_vehicle_types, status) "
                "VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING *",
                uuid4(), as_uuid(data["parking_id"]), data["zone_id"], data["zone_name"], data["space_code"],
                data["allowed_vehicle_types"], data["status"],
            )
        return _serialize(row)

    async def find_by_id(self, space_id: str):
        async with PostgresDB.get_pool().acquire() as connection:
            row = await connection.fetchrow("SELECT * FROM parking_spaces WHERE id=$1", as_uuid(space_id))
        return _serialize(row)

    async def find_by_parking(self, parking_id: str, status: str | None = None, vehicle_type: str | None = None):
        conditions = ["parking_id=$1"]
        values = [as_uuid(parking_id)]
        if status:
            values.append(status)
            conditions.append(f"status=${len(values)}")
        if vehicle_type:
            values.append(vehicle_type)
            conditions.append(f"${len(values)} = ANY(allowed_vehicle_types)")
        async with PostgresDB.get_pool().acquire() as connection:
            rows = await connection.fetch(
                f"SELECT * FROM parking_spaces WHERE {' AND '.join(conditions)} ORDER BY space_code", *values
            )
        return [_serialize(row) for row in rows]

    @translate_constraint_errors
    async def update(self, space_id: str, data: dict):
        if not data:
            return await self.find_by_id(space_id)
        allowed = {"zone_id", "zone_name", "space_code", "allowed_vehicle_types", "status"}
        if not set(data) <= allowed:
            raise ValueError("Unsupported parking space fields")
        values = [as_uuid(space_id), *data.values()]
        assignments = ", ".join(f"{field}=${index}" for index, field in enumerate(data, start=2))
        async with PostgresDB.get_pool().acquire() as connection:
            row = await connection.fetchrow(
                f"UPDATE parking_spaces SET {assignments}, updated_at=NOW() WHERE id=$1 RETURNING *", *values
            )
        return _serialize(row)

    async def delete(self, space_id: str):
        async with PostgresDB.get_pool().acquire() as connection:
            result = await connection.execute("DELETE FROM parking_spaces WHERE id=$1", as_uuid(space_id))
        return result.endswith(" 1")
