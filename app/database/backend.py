from app.config.settings import settings


class MongoBackend:
    async def connect(self):
        from app.database.mongodb import MongoDB
        from app.repositories.user_repository import UserRepository
        from app.repositories.vehicle_repository import VehicleRepository

        await MongoDB.connect()
        self.user_repository = UserRepository()
        self.vehicle_repository = VehicleRepository()

    async def close(self):
        from app.database.mongodb import MongoDB

        await MongoDB.close()


class PostgresBackend:
    async def connect(self):
        from app.database.postgres import PostgresDB
        from app.repositories.postgres_user_repository import PostgresUserRepository
        from app.repositories.postgres_vehicle_repository import PostgresVehicleRepository

        await PostgresDB.connect()
        self.user_repository = PostgresUserRepository()
        self.vehicle_repository = PostgresVehicleRepository()

    async def close(self):
        from app.database.postgres import PostgresDB

        await PostgresDB.close()


def create_backend(name: str | None = None):
    backend = (name or settings.DATABASE_BACKEND).strip().lower()
    if backend == "mongodb":
        return MongoBackend()
    if backend in {"postgres", "postgresql"}:
        return PostgresBackend()
    raise ValueError("DATABASE_BACKEND debe ser mongodb o postgresql")
