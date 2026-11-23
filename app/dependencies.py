"""Composition root for application services injected into API controllers."""
from fastapi import Request

from app.services.reservationservice.reservation_service import ReservationService
from app.services.reservationservice.reservation_service_impl import ReservationServiceImpl
from app.services.tariffservice.tariff_service import TariffService
from app.services.tariffservice.tariff_service_impl import TariffServiceImpl
from app.services.parkingservice.parking_service import ParkingService
from app.services.parkingservice.parking_service_impl import ParkingServiceImpl
from app.services.parkingspaceservice.parking_space_service import ParkingSpaceService
from app.services.parkingspaceservice.parking_space_service_impl import ParkingSpaceServiceImpl
from app.services.userservice.user_service import UserService
from app.services.userservice.user_service_impl import UserServiceImpl
from app.services.vehicleservice.vehicle_service import VehicleService
from app.services.vehicleservice.vehicle_service_impl import VehicleServiceImpl
from app.services.parkingsessionservice.parking_session_service import ParkingSessionService
from app.services.parkingsessionservice.parking_session_service_impl import ParkingSessionServiceImpl


def get_parking_service(request: Request) -> ParkingService:
    return ParkingServiceImpl(request.app.state.backend.parking_repository)


def get_parking_space_service(request: Request) -> ParkingSpaceService:
    backend = request.app.state.backend
    return ParkingSpaceServiceImpl(backend.parking_repository, backend.parking_space_repository,
                                   cache=request.app.state.redis_cache)


def get_user_service(request: Request) -> UserService:
    backend = request.app.state.backend
    return UserServiceImpl(backend.user_repository, backend.vehicle_repository)


def get_vehicle_service(request: Request) -> VehicleService:
    backend = request.app.state.backend
    return VehicleServiceImpl(backend.user_repository, backend.vehicle_repository)


def get_tariff_service(request: Request) -> TariffService:
    backend = request.app.state.backend
    return TariffServiceImpl(backend.parking_repository, backend.tariff_repository)


def get_reservation_service(request: Request) -> ReservationService:
    backend = request.app.state.backend
    return ReservationServiceImpl(
        backend.parking_space_repository,
        backend.vehicle_repository,
        backend.tariff_repository,
        backend.reservation_repository,
        cache=request.app.state.redis_cache,
    )


def get_parking_session_service(request: Request) -> ParkingSessionService:
    backend = request.app.state.backend
    return ParkingSessionServiceImpl(
        backend.parking_space_repository,
        backend.vehicle_repository,
        backend.tariff_repository,
        backend.parking_session_repository,
        cache=request.app.state.redis_cache,
    )
