from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from app.auth import get_current_user, require_admin

from app.schemas.parking_space_schema import (
    ParkingSpaceCreate,
    ParkingSpaceResponse,
    ParkingSpaceUpdate,
    normalize_vehicle_type,
)
from app.services.parkingspaceservice.parking_space_service import ParkingSpaceService
from app.services.parkingspaceservice.parking_space_service_impl import (
    ParkingNotFoundError,
    ParkingSpaceAlreadyExistsError,
    ParkingSpaceNotFoundError,
    ParkingSpaceServiceImpl,
    ParkingSpaceValidationError,
)

router = APIRouter(tags=["Parking spaces"])


def get_service(request: Request) -> ParkingSpaceService:
    backend = request.app.state.backend
    return ParkingSpaceServiceImpl(
        backend.parking_repository,
        backend.parking_space_repository,
        cache=request.app.state.redis_cache,
    )


def _raise_http_error(exc):
    if isinstance(exc, (ParkingNotFoundError, ParkingSpaceNotFoundError)):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ParkingSpaceAlreadyExistsError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, ParkingSpaceValidationError):
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/parkings/{parking_id}/spaces",
    response_model=ParkingSpaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_space(
    parking_id: str,
    data: ParkingSpaceCreate,
    service: ParkingSpaceService = Depends(get_service),
    _admin=Depends(require_admin),
):
    try:
        return await service.create(parking_id, data)
    except (ParkingNotFoundError, ParkingSpaceAlreadyExistsError, ParkingSpaceValidationError) as exc:
        _raise_http_error(exc)


@router.get("/parkings/{parking_id}/spaces", response_model=list[ParkingSpaceResponse])
async def list_spaces(
    parking_id: str,
    status_filter: Literal["available", "occupied", "reserved", "out_of_service"] | None = Query(
        default=None, alias="status"
    ),
    vehicle_type: Literal["carro", "moto", "bicicleta", "car", "motorcycle", "bicycle"] | None = None,
    service: ParkingSpaceService = Depends(get_service),
    _user=Depends(get_current_user),
):
    try:
        normalized_type = normalize_vehicle_type(vehicle_type) if vehicle_type else None
        return await service.find_by_parking(parking_id, status=status_filter, vehicle_type=normalized_type)
    except ParkingNotFoundError as exc:
        _raise_http_error(exc)


@router.get("/parkings/{parking_id}/availability")
async def get_availability(
    parking_id: str,
    vehicle_type: Literal["carro", "moto", "bicicleta", "car", "motorcycle", "bicycle"] | None = None,
    service: ParkingSpaceService = Depends(get_service),
    _user=Depends(get_current_user),
):
    try:
        normalized_type = normalize_vehicle_type(vehicle_type) if vehicle_type else None
        return await service.availability(parking_id, vehicle_type=normalized_type)
    except ParkingNotFoundError as exc:
        _raise_http_error(exc)


@router.get("/parking-spaces/{space_id}", response_model=ParkingSpaceResponse)
async def get_space(space_id: str, service: ParkingSpaceService = Depends(get_service), _user=Depends(get_current_user)):
    try:
        return await service.find_by_id(space_id)
    except ParkingSpaceNotFoundError as exc:
        _raise_http_error(exc)


@router.patch("/parking-spaces/{space_id}", response_model=ParkingSpaceResponse)
async def update_space(
    space_id: str,
    data: ParkingSpaceUpdate,
    service: ParkingSpaceService = Depends(get_service),
    _admin=Depends(require_admin),
):
    try:
        return await service.update(space_id, data)
    except (ParkingNotFoundError, ParkingSpaceNotFoundError, ParkingSpaceAlreadyExistsError, ParkingSpaceValidationError) as exc:
        _raise_http_error(exc)


@router.delete("/parking-spaces/{space_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_space(space_id: str, service: ParkingSpaceService = Depends(get_service), _admin=Depends(require_admin)):
    try:
        await service.delete(space_id)
    except ParkingSpaceNotFoundError as exc:
        _raise_http_error(exc)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
