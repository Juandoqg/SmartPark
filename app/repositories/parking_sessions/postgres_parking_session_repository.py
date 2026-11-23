import json
from uuid import uuid4

from app.database.postgres import PostgresDB, as_uuid, translate_constraint_errors
from app.repositories.ports import RepositoryConflictError
from app.repositories.parking_sessions.parking_session_repository import ParkingSessionRepository


def _row(row):
    if row is None:
        return None
    result = dict(row)
    for key in ("id", "parking_id", "space_id", "user_id", "created_by", "vehicle_id", "tariff_id"):
        if result.get(key) is not None:
            result[key] = str(result[key])
    if isinstance(result.get("tariff_snapshot"), str):
        result["tariff_snapshot"] = json.loads(result["tariff_snapshot"])
    return result


class PostgresParkingSessionRepository(ParkingSessionRepository):
    async def find_by_idempotency_key(self, user_id, key):
        async with PostgresDB.get_pool().acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM parking_sessions WHERE created_by=$1 AND idempotency_key=$2",
                                      as_uuid(user_id), key)
        return _row(row)

    async def find_active_by_space(self, space_id):
        async with PostgresDB.get_pool().acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM parking_sessions WHERE space_id=$1 AND status='active'", as_uuid(space_id))
        return _row(row)

    async def find_active_by_vehicle(self, vehicle_id):
        async with PostgresDB.get_pool().acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM parking_sessions WHERE vehicle_id=$1 AND status='active'", as_uuid(vehicle_id))
        return _row(row)

    @translate_constraint_errors
    async def create_active(self, data):
        async with PostgresDB.get_pool().acquire() as conn:
            async with conn.transaction():
                space_id = as_uuid(data["space_id"])
                await conn.execute("SELECT pg_advisory_xact_lock(hashtextextended($1, 0))", str(space_id))
                claimed = await conn.fetchrow("UPDATE parking_spaces SET status='occupied', updated_at=$2 "
                                              "WHERE id=$1 AND status='available' RETURNING id", space_id, data["entry_at"])
                if claimed is None:
                    raise RepositoryConflictError("El espacio dejó de estar disponible")
                row = await conn.fetchrow("""INSERT INTO parking_sessions
                    (id, parking_id, space_id, user_id, created_by, vehicle_id, tariff_id, tariff_snapshot,
                     entry_at, status, payment_status, idempotency_key, request_fingerprint, created_at, updated_at)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8::jsonb,$9,'active','pending',$10,$11,$9,$9) RETURNING *""",
                    uuid4(), as_uuid(data["parking_id"]), space_id, as_uuid(data["user_id"]), as_uuid(data["created_by"]),
                    as_uuid(data["vehicle_id"]), as_uuid(data["tariff_id"]),
                    json.dumps(data["tariff_snapshot"], default=str), data["entry_at"],
                    data["idempotency_key"], data["request_fingerprint"])
        return _row(row)

    async def find_by_id(self, session_id):
        async with PostgresDB.get_pool().acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM parking_sessions WHERE id=$1", as_uuid(session_id))
        return _row(row)

    async def find(self, user_id=None, parking_id=None, status=None):
        conditions, values = [], []
        for column, value in (("user_id", user_id), ("parking_id", parking_id), ("status", status)):
            if value is not None:
                values.append(as_uuid(value) if column in {"user_id", "parking_id"} else value)
                conditions.append(f"{column}=${len(values)}")
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        async with PostgresDB.get_pool().acquire() as conn:
            rows = await conn.fetch(f"SELECT * FROM parking_sessions{where} ORDER BY entry_at DESC", *values)
        return [_row(row) for row in rows]

    async def close_active(self, session_id, exit_at, duration_minutes, total_amount):
        async with PostgresDB.get_pool().acquire() as conn:
            async with conn.transaction():
                current = await conn.fetchrow("UPDATE parking_sessions SET status='completed', exit_at=$2, "
                    "duration_minutes=$3, total_amount=$4, payment_status='pending', updated_at=$2 "
                    "WHERE id=$1 AND status='active' RETURNING *", as_uuid(session_id), exit_at, duration_minutes, total_amount)
                if current is None:
                    return None
                await conn.execute("UPDATE parking_spaces SET status='available', updated_at=$2 "
                                   "WHERE id=$1 AND status='occupied'", current["space_id"], exit_at)
        return _row(current)
