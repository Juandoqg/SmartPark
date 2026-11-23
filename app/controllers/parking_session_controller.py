from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user
from app.dependencies import get_parking_session_service
from app.schemas.parking_session_schema import ParkingSessionEntry, ParkingSessionResponse
from app.services.parkingsessionservice.parking_session_errors import ParkingSessionError
from app.services.parkingsessionservice.parking_session_service import ParkingSessionService


router = APIRouter(prefix="/sessions", tags=["Parking sessions"])


@router.post("/entry", response_model=ParkingSessionResponse, status_code=status.HTTP_201_CREATED)
async def register_entry(
    data: ParkingSessionEntry,
    service: ParkingSessionService = Depends(get_parking_session_service),
    user=Depends(get_current_user),
):
    try:
        return await service.entry(data, user)
    except ParkingSessionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/{session_id}/exit", response_model=ParkingSessionResponse)
async def register_exit(
    session_id: str,
    service: ParkingSessionService = Depends(get_parking_session_service),
    user=Depends(get_current_user),
):
    try:
        return await service.exit(session_id, user)
    except ParkingSessionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("", response_model=list[ParkingSessionResponse])
async def list_sessions(
    parking_id: str | None = None,
    session_status: Literal["active", "completed"] | None = Query(default=None, alias="status"),
    service: ParkingSessionService = Depends(get_parking_session_service),
    user=Depends(get_current_user),
):
    return await service.list_sessions(user, parking_id=parking_id, status=session_status)
