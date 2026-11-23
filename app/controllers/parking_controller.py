from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.auth import get_current_user, require_admin
from app.dependencies import get_parking_service

from app.schemas.parking_schema import ParkingCreate, ParkingResponse, ParkingUpdate
from app.services.parkingservice.parking_service import ParkingService
from app.services.parkingservice.parking_errors import ParkingNotFoundError


router = APIRouter(prefix="/parkings", tags=["Parkings"])


@router.post("", response_model=ParkingResponse, status_code=status.HTTP_201_CREATED)
async def create_parking(
    parking: ParkingCreate,
    service: ParkingService = Depends(get_parking_service),
    _admin=Depends(require_admin),
):
    return await service.create(parking)


@router.get("", response_model=list[ParkingResponse])
async def find_all_parkings(service: ParkingService = Depends(get_parking_service), _user=Depends(get_current_user)):
    return await service.find_all()


@router.get("/{parking_id}", response_model=ParkingResponse)
async def find_parking_by_id(
    parking_id: str,
    service: ParkingService = Depends(get_parking_service),
    _user=Depends(get_current_user),
):
    try:
        return await service.find_by_id(parking_id)
    except ParkingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{parking_id}", response_model=ParkingResponse)
async def update_parking(
    parking_id: str,
    data: ParkingUpdate,
    service: ParkingService = Depends(get_parking_service),
    _admin=Depends(require_admin),
):
    try:
        return await service.update(parking_id, data)
    except ParkingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{parking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parking(
    parking_id: str,
    service: ParkingService = Depends(get_parking_service),
    _admin=Depends(require_admin),
):
    try:
        await service.delete(parking_id)
    except ParkingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
