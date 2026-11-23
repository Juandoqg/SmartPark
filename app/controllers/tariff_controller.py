from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.auth import get_current_user, require_manager
from app.dependencies import get_tariff_service
from app.schemas.tariff_schema import TariffCreate, TariffResponse, TariffUpdate
from app.services.tariffservice.tariff_service import TariffService
from app.services.tariffservice.tariff_errors import TariffNotFoundError, TariffParkingNotFoundError, TariffValidationError

router = APIRouter(prefix="/parkings/{parking_id}/tariffs", tags=["Tariffs"])


@router.post("", response_model=TariffResponse, status_code=status.HTTP_201_CREATED)
async def create_tariff(parking_id: str, data: TariffCreate, service: TariffService = Depends(get_tariff_service), _manager=Depends(require_manager)):
    try:
        return await service.create(parking_id, data)
    except TariffParkingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TariffValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=list[TariffResponse])
async def list_tariffs(parking_id: str, active: bool | None = Query(default=None), service: TariffService = Depends(get_tariff_service), _user=Depends(get_current_user)):
    try:
        return await service.list_by_parking(parking_id, active)
    except TariffParkingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{tariff_id}", response_model=TariffResponse)
async def update_tariff(parking_id: str, tariff_id: str, data: TariffUpdate, service: TariffService = Depends(get_tariff_service), _manager=Depends(require_manager)):
    try:
        return await service.update(parking_id, tariff_id, data)
    except TariffNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
