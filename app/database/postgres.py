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
                    password_hash TEXT,
                    role VARCHAR(20) NOT NULL DEFAULT 'user',
                    created_at TIMESTAMPTZ NOT NULL
                )
            """)
            await connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT")
            await connection.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user'")
            if settings.ADMIN_EMAIL.strip():
                await connection.execute(
                    "UPDATE users SET role='admin' WHERE lower(email)=lower($1)", settings.ADMIN_EMAIL.strip()
                )
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
                    zone_id VARCHAR(50) NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    level INTEGER NOT NULL DEFAULT 1,
                    description VARCHAR(150),
                    PRIMARY KEY (parking_id, name)
                )
            """)
            await connection.execute("ALTER TABLE parking_zones ADD COLUMN IF NOT EXISTS zone_id VARCHAR(50)")
            await connection.execute("ALTER TABLE parking_zones ADD COLUMN IF NOT EXISTS level INTEGER")
            await connection.execute("UPDATE parking_zones SET zone_id=name WHERE zone_id IS NULL")
            await connection.execute("UPDATE parking_zones SET level=1 WHERE level IS NULL")
            await connection.execute("ALTER TABLE parking_zones ALTER COLUMN zone_id SET NOT NULL")
            await connection.execute("ALTER TABLE parking_zones ALTER COLUMN level SET NOT NULL")
            await connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS unique_zone_id_per_parking ON parking_zones(parking_id, zone_id)"
            )
            await connection.execute("CREATE INDEX IF NOT EXISTS parkings_by_city_name ON parkings(city, name)")
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS parking_spaces (
                    id UUID PRIMARY KEY,
                    parking_id UUID NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
                    zone_id VARCHAR(50) NOT NULL,
                    zone_name VARCHAR(50) NOT NULL,
                    space_code VARCHAR(30) NOT NULL,
                    allowed_vehicle_types TEXT[] NOT NULL,
                    status VARCHAR(24) NOT NULL DEFAULT 'available'
                        CHECK (status IN ('available', 'occupied', 'reserved', 'out_of_service')),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (parking_id, space_code)
                )
            """)
            await connection.execute("ALTER TABLE parking_spaces ADD COLUMN IF NOT EXISTS zone_id VARCHAR(50)")
            await connection.execute("""
                UPDATE parking_spaces AS spaces SET zone_id=zones.zone_id
                FROM parking_zones AS zones
                WHERE spaces.zone_id IS NULL
                  AND spaces.parking_id=zones.parking_id
                  AND spaces.zone_name=zones.name
            """)
            await connection.execute("UPDATE parking_spaces SET zone_id=zone_name WHERE zone_id IS NULL")
            await connection.execute("ALTER TABLE parking_spaces ALTER COLUMN zone_id SET NOT NULL")
            await connection.execute(
                "CREATE INDEX IF NOT EXISTS spaces_by_parking_zone_status ON parking_spaces(parking_id, zone_id, status)"
            )
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS tariffs (
                    id UUID PRIMARY KEY,
                    parking_id UUID NOT NULL REFERENCES parkings(id) ON DELETE CASCADE,
                    name VARCHAR(80) NOT NULL,
                    vehicle_type VARCHAR(20) NOT NULL CHECK (vehicle_type IN ('carro','moto','bicicleta')),
                    currency CHAR(3) NOT NULL DEFAULT 'COP',
                    hourly_rate NUMERIC(12,2) NOT NULL CHECK (hourly_rate > 0),
                    reservation_rate NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (reservation_rate >= 0),
                    billing_increment_minutes INTEGER NOT NULL DEFAULT 60 CHECK (billing_increment_minutes BETWEEN 1 AND 1440),
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            await connection.execute("CREATE INDEX IF NOT EXISTS tariffs_by_parking_vehicle_status ON tariffs(parking_id, vehicle_type, active)")
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS reservations (
                    id UUID PRIMARY KEY,
                    parking_id UUID NOT NULL REFERENCES parkings(id) ON DELETE RESTRICT,
                    space_id UUID NOT NULL REFERENCES parking_spaces(id) ON DELETE RESTRICT,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
                    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
                    vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
                    tariff_id UUID NOT NULL REFERENCES tariffs(id) ON DELETE RESTRICT,
                    tariff_snapshot JSONB NOT NULL,
                    estimated_total NUMERIC(12,2) NOT NULL CHECK (estimated_total >= 0),
                    starts_at TIMESTAMPTZ NOT NULL,
                    ends_at TIMESTAMPTZ NOT NULL CHECK (ends_at > starts_at),
                    status VARCHAR(20) NOT NULL DEFAULT 'confirmed' CHECK (status IN ('confirmed','cancelled','completed')),
                    idempotency_key VARCHAR(128) NOT NULL,
                    request_fingerprint CHAR(64) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (created_by, idempotency_key)
                )
            """)
            await connection.execute("CREATE INDEX IF NOT EXISTS reservations_by_space_time_status ON reservations(space_id, starts_at, ends_at, status)")
            await connection.execute("CREATE INDEX IF NOT EXISTS reservations_by_user_date ON reservations(user_id, starts_at DESC)")
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS parking_sessions (
                    id UUID PRIMARY KEY,
                    parking_id UUID NOT NULL REFERENCES parkings(id) ON DELETE RESTRICT,
                    space_id UUID NOT NULL REFERENCES parking_spaces(id) ON DELETE RESTRICT,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
                    vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
                    tariff_id UUID NOT NULL REFERENCES tariffs(id) ON DELETE RESTRICT,
                    tariff_snapshot JSONB NOT NULL,
                    entry_at TIMESTAMPTZ NOT NULL,
                    exit_at TIMESTAMPTZ,
                    duration_minutes INTEGER CHECK (duration_minutes IS NULL OR duration_minutes >= 0),
                    total_amount NUMERIC(12,2) CHECK (total_amount IS NULL OR total_amount >= 0),
                    status VARCHAR(20) NOT NULL CHECK (status IN ('active','completed')),
                    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (payment_status IN ('pending','paid','failed')),
                    idempotency_key VARCHAR(128) NOT NULL,
                    request_fingerprint CHAR(64) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CHECK ((status='active' AND exit_at IS NULL AND total_amount IS NULL)
                        OR (status='completed' AND exit_at IS NOT NULL AND total_amount IS NOT NULL)),
                    UNIQUE (user_id, idempotency_key)
                )
            """)
            await connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_active_session_per_space ON parking_sessions(space_id) WHERE status='active'")
            await connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_active_session_per_vehicle ON parking_sessions(vehicle_id) WHERE status='active'")
            await connection.execute("CREATE INDEX IF NOT EXISTS sessions_by_parking_entry_date ON parking_sessions(parking_id, entry_at DESC)")
            await connection.execute("CREATE INDEX IF NOT EXISTS sessions_by_user_entry_date ON parking_sessions(user_id, entry_at DESC)")

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
