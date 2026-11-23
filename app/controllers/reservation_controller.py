from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user
from app.dependencies import get_reservation_service
from app.schemas.reservation_schema import ReservationCreate, ReservationResponse
from app.services.reservationservice.reservation_service import ReservationService
from app.services.reservationservice.reservation_errors import ReservationError

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("", response_model=ReservationResponse, status_code=201)
async def create_reservation(data: ReservationCreate, service: ReservationService = Depends(get_reservation_service), user=Depends(get_current_user)):
    try:
        return await service.create(data, user)
    except ReservationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("", response_model=list[ReservationResponse])
async def list_reservations(service: ReservationService = Depends(get_reservation_service), user=Depends(get_current_user)):
    return await service.list_mine(user)


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
async def cancel_reservation(reservation_id: str, service: ReservationService = Depends(get_reservation_service), user=Depends(get_current_user)):
    try:
        return await service.cancel(reservation_id, user)
    except ReservationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
