from uuid import uuid4

from app.database.postgres import PostgresDB, as_uuid, translate_constraint_errors
from app.repositories.vehicles.vehicle_repository import VehicleRepository


def _vehicle(row):
    if row is None:
        return None
    result = dict(row)
    result["id"] = str(result["id"])
    result["user_id"] = str(result["user_id"])
    return result


class PostgresVehicleRepository(VehicleRepository):
    @translate_constraint_errors
    async def create(self, data):
        async with PostgresDB.get_pool().acquire() as connection:
            row = await connection.fetchrow(
                "INSERT INTO vehicles (id, plate, vehicle_type, user_id) VALUES ($1,$2,$3,$4) "
                "RETURNING id, plate, vehicle_type, user_id",
                uuid4(), data["plate"], data["vehicle_type"], as_uuid(data["user_id"]),
            )
        return _vehicle(row)

    async def find_by_id(self, vehicle_id):
        async with PostgresDB.get_pool().acquire() as connection:
            return _vehicle(await connection.fetchrow(
                "SELECT id, plate, vehicle_type, user_id FROM vehicles WHERE id=$1", as_uuid(vehicle_id)
            ))

    async def find_by_plate(self, plate):
        async with PostgresDB.get_pool().acquire() as connection:
            return _vehicle(await connection.fetchrow(
                "SELECT id, plate, vehicle_type, user_id FROM vehicles WHERE plate=$1", plate
            ))

    async def find_by_user(self, user_id):
        async with PostgresDB.get_pool().acquire() as connection:
            rows = await connection.fetch(
                "SELECT id, plate, vehicle_type, user_id FROM vehicles WHERE user_id=$1 ORDER BY plate", as_uuid(user_id)
            )
        return [_vehicle(row) for row in rows]

    async def find_all(self):
        async with PostgresDB.get_pool().acquire() as connection:
            rows = await connection.fetch("SELECT id, plate, vehicle_type, user_id FROM vehicles ORDER BY plate")
        return [_vehicle(row) for row in rows]

    @translate_constraint_errors
    async def update(self, vehicle_id, data):
        if not data:
            return await self.find_by_id(vehicle_id)
        allowed = {"plate", "vehicle_type", "user_id"}
        if not set(data) <= allowed:
            raise ValueError("Unsupported vehicle fields")
        values = [as_uuid(vehicle_id)]
        for field, value in data.items():
            values.append(as_uuid(value) if field == "user_id" else value)
        assignments = ", ".join(f"{field}=${index}" for index, field in enumerate(data, start=2))
        async with PostgresDB.get_pool().acquire() as connection:
            row = await connection.fetchrow(
                f"UPDATE vehicles SET {assignments} WHERE id=$1 RETURNING id, plate, vehicle_type, user_id", *values
            )
        return _vehicle(row)

    async def delete(self, vehicle_id):
        async with PostgresDB.get_pool().acquire() as connection:
            status = await connection.execute("DELETE FROM vehicles WHERE id=$1", as_uuid(vehicle_id))
        return status.endswith("1")

    async def count_by_user(self, user_id):
        async with PostgresDB.get_pool().acquire() as connection:
            return await connection.fetchval("SELECT count(*) FROM vehicles WHERE user_id=$1", as_uuid(user_id))
