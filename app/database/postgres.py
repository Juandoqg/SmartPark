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
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS parkings (
                    id UUID PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    address VARCHAR(200) NOT NULL,
                    city VARCHAR(80) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS parking_zones (
                    parking_id UUID NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
                    name VARCHAR(50) NOT NULL,
                    description VARCHAR(150),
                    PRIMARY KEY (parking_id, name)
                )
            """)
            await connection.execute("CREATE INDEX IF NOT EXISTS parkings_by_city_name ON parkings(city, name)")

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
