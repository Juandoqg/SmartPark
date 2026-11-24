from app.config.settings import settings


class MongoBackend:
    async def connect(self):
        from app.database.mongodb import MongoDB
        from app.repositories.users.mongo_user_repository import MongoUserRepository
        from app.repositories.vehicles.mongo_vehicle_repository import MongoVehicleRepository
        from app.repositories.parkings.mongo_parking_repository import MongoParkingRepository
        from app.repositories.parking_spaces.mongo_parking_space_repository import MongoParkingSpaceRepository
        from app.repositories.tariffs.mongo_tariff_repository import MongoTariffRepository
        from app.repositories.reservations.mongo_reservation_repository import MongoReservationRepository
        from app.repositories.parking_sessions.mongo_parking_session_repository import MongoParkingSessionRepository
        from app.repositories.reports.mongo_report_repository import MongoReportRepository

        await MongoDB.connect()
        self.user_repository = MongoUserRepository()
        self.vehicle_repository = MongoVehicleRepository()
        self.parking_repository = MongoParkingRepository()
        self.parking_space_repository = MongoParkingSpaceRepository()
        self.tariff_repository = MongoTariffRepository()
        self.reservation_repository = MongoReservationRepository()
        self.parking_session_repository = MongoParkingSessionRepository()
        self.report_repository = MongoReportRepository()

    async def close(self):
        from app.database.mongodb import MongoDB

        await MongoDB.close()


class PostgresBackend:
    async def connect(self):
        from app.database.postgres import PostgresDB
        from app.repositories.users.postgres_user_repository import PostgresUserRepository
        from app.repositories.vehicles.postgres_vehicle_repository import PostgresVehicleRepository
        from app.repositories.parkings.postgres_parking_repository import PostgresParkingRepository
        from app.repositories.parking_spaces.postgres_parking_space_repository import PostgresParkingSpaceRepository
        from app.repositories.tariffs.postgres_tariff_repository import PostgresTariffRepository
        from app.repositories.reservations.postgres_reservation_repository import PostgresReservationRepository
        from app.repositories.parking_sessions.postgres_parking_session_repository import PostgresParkingSessionRepository

        await PostgresDB.connect()
        self.user_repository = PostgresUserRepository()
        self.vehicle_repository = PostgresVehicleRepository()
        self.parking_repository = PostgresParkingRepository()
        self.parking_space_repository = PostgresParkingSpaceRepository()
        self.tariff_repository = PostgresTariffRepository()
        self.reservation_repository = PostgresReservationRepository()
        self.parking_session_repository = PostgresParkingSessionRepository()
        # Reports are implemented as MongoDB aggregations only.
        self.report_repository = None

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
