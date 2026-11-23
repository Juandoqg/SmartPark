from uuid import uuid4
from app.database.postgres import PostgresDB, as_uuid, translate_constraint_errors
from app.repositories.tariffs.tariff_repository import TariffRepository


def _row(row):
    if row is None:
        return None
    item = dict(row)
    item["id"] = str(item.pop("id"))
    item["parking_id"] = str(item["parking_id"])
    return item


class PostgresTariffRepository(TariffRepository):
    @translate_constraint_errors
    async def create(self, data):
        async with PostgresDB.get_pool().acquire() as conn:
            row = await conn.fetchrow("""INSERT INTO tariffs
                (id, parking_id, name, vehicle_type, currency, hourly_rate, reservation_rate, billing_increment_minutes, active)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING *""",
                uuid4(), as_uuid(data["parking_id"]), data["name"], data["vehicle_type"], data["currency"],
                data["hourly_rate"], data["reservation_rate"], data["billing_increment_minutes"], data["active"])
        return _row(row)

    async def find_by_id(self, tariff_id):
        async with PostgresDB.get_pool().acquire() as conn:
            return _row(await conn.fetchrow("SELECT * FROM tariffs WHERE id=$1", as_uuid(tariff_id)))

    async def find_by_parking(self, parking_id, active=None):
        async with PostgresDB.get_pool().acquire() as conn:
            rows = await conn.fetch("SELECT * FROM tariffs WHERE parking_id=$1 AND ($2::boolean IS NULL OR active=$2) ORDER BY name",
                                    as_uuid(parking_id), active)
        return [_row(row) for row in rows]

    @translate_constraint_errors
    async def update(self, tariff_id, data):
        if not data:
            return await self.find_by_id(tariff_id)
        allowed = {"name", "hourly_rate", "reservation_rate", "billing_increment_minutes", "active"}
        if not set(data) <= allowed:
            raise ValueError("Unsupported tariff fields")
        values = [as_uuid(tariff_id), *data.values()]
        assignments = ", ".join(f"{key}=${i}" for i, key in enumerate(data, 2))
        async with PostgresDB.get_pool().acquire() as conn:
            row = await conn.fetchrow(f"UPDATE tariffs SET {assignments}, updated_at=NOW() WHERE id=$1 RETURNING *", *values)
        return _row(row)
