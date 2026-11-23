import json
from datetime import datetime, timezone
from uuid import uuid4
from app.database.postgres import PostgresDB, as_uuid, translate_constraint_errors
from app.repositories.ports import RepositoryConflictError
from app.repositories.reservations.reservation_repository import ReservationRepository


def _row(row):
    if row is None:
        return None
    item = dict(row)
    for key in ("id", "parking_id", "space_id", "user_id", "vehicle_id", "tariff_id"):
        if item.get(key) is not None:
            item[key] = str(item[key])
    return item


class PostgresReservationRepository(ReservationRepository):
    async def find_by_idempotency_key(self, user_id, key):
        async with PostgresDB.get_pool().acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM reservations WHERE user_id=$1 AND idempotency_key=$2", as_uuid(user_id), key)
        return _row(row)

    async def has_overlap(self, space_id, starts_at, ends_at):
        async with PostgresDB.get_pool().acquire() as conn:
            return await conn.fetchval("""SELECT EXISTS(SELECT 1 FROM reservations WHERE space_id=$1 AND status='confirmed'
                AND starts_at < $3 AND ends_at > $2)""", as_uuid(space_id), starts_at, ends_at)

    @translate_constraint_errors
    async def create(self, data):
        async with PostgresDB.get_pool().acquire() as conn:
            async with conn.transaction():
                await conn.execute("SELECT pg_advisory_xact_lock(hashtextextended($1, 0))", data["space_id"])
                if await conn.fetchval("""SELECT EXISTS(SELECT 1 FROM reservations WHERE space_id=$1 AND status='confirmed'
                    AND starts_at < $3 AND ends_at > $2)""", as_uuid(data["space_id"]), data["starts_at"], data["ends_at"]):
                    raise RepositoryConflictError("El espacio ya está reservado en ese horario")
                row = await conn.fetchrow("""INSERT INTO reservations
                    (id, parking_id, space_id, user_id, vehicle_id, tariff_id, tariff_snapshot, estimated_total,
                     starts_at, ends_at, status, idempotency_key, request_fingerprint)
                    VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8,$9,$10,$11,$12,$13) RETURNING *""",
                    uuid4(), as_uuid(data["parking_id"]), as_uuid(data["space_id"]), as_uuid(data["user_id"]),
                    as_uuid(data["vehicle_id"]), as_uuid(data["tariff_id"]), json.dumps(data["tariff_snapshot"], default=str),
                    data["estimated_total"], data["starts_at"], data["ends_at"], data["status"],
                    data["idempotency_key"], data["request_fingerprint"])
        return _row(row)

    async def find_by_user(self, user_id):
        async with PostgresDB.get_pool().acquire() as conn:
            rows = await conn.fetch("SELECT * FROM reservations WHERE user_id=$1 ORDER BY starts_at DESC", as_uuid(user_id))
        return [_row(row) for row in rows]

    async def cancel(self, reservation_id, user_id):
        async with PostgresDB.get_pool().acquire() as conn:
            row = await conn.fetchrow("""UPDATE reservations SET status='cancelled', updated_at=NOW()
                WHERE id=$1 AND user_id=$2 AND status='confirmed' RETURNING *""", as_uuid(reservation_id), as_uuid(user_id))
        return _row(row)
