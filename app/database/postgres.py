from functools import wraps
from uuid import UUID

import asyncpg

from app.config.settings import settings
from app.repositories.ports import RepositoryConflictError


def translate_constraint_errors(method):
    @wraps(method)
    async def wrapped(*args, **kwargs):
        try:
            return await method(*args, **kwargs)
        except (asyncpg.UniqueViolationError, asyncpg.ForeignKeyViolationError) as exc:
            raise RepositoryConflictError("PostgreSQL rechazó la operación por una restricción") from exc
    return wrapped


class PostgresDB:
    pool: asyncpg.Pool | None = None

    @classmethod
    async def connect(cls):
        cls.pool = await asyncpg.create_pool(
            settings.POSTGRES_URL,
            min_size=1,
            max_size=10,
            command_timeout=10,
        )
        async with cls.pool.acquire() as connection:
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL,
                    email VARCHAR(320) NOT NULL UNIQUE,
                    phone VARCHAR(20),
                    created_at TIMESTAMPTZ NOT NULL
                )
            """)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    id UUID PRIMARY KEY,
                    plate VARCHAR(10) UNIQUE,
                    vehicle_type VARCHAR(30) NOT NULL,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT
                )
            """)
            # Keep existing development databases compatible with bicycle records without plates.
            await connection.execute("ALTER TABLE vehicles ALTER COLUMN plate DROP NOT NULL")
            await connection.execute("CREATE INDEX IF NOT EXISTS vehicles_by_user ON vehicles(user_id)")

    @classmethod
    def get_pool(cls) -> asyncpg.Pool:
        if cls.pool is None:
            raise RuntimeError("PostgreSQL is not connected")
        return cls.pool

    @classmethod
    async def close(cls):
        if cls.pool is not None:
            await cls.pool.close()
            cls.pool = None


def as_uuid(value: str) -> UUID:
    return UUID(str(value))
