import re
from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import require_admin
from app.dependencies import get_vehicle_service
from app.schemas.vehicle_schema import VehicleCreate, VehicleResponse, VehicleUpdate
from app.services.vehicleservice.vehicle_service import VehicleService
from app.services.vehicleservice.vehicle_errors import (
    UserNotFoundError, VehicleAlreadyExistsError, VehicleNotFoundError,
    VehicleValidationError,
)

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])
def handle_error(exc):
    if isinstance(exc, VehicleAlreadyExistsError): raise HTTPException(409, detail=str(exc)) from exc
    if isinstance(exc, (UserNotFoundError, VehicleNotFoundError)): raise HTTPException(404, detail=str(exc)) from exc
    if isinstance(exc, VehicleValidationError): raise HTTPException(422, detail=str(exc)) from exc

@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(vehicle: VehicleCreate, service: VehicleService = Depends(get_vehicle_service), _admin=Depends(require_admin)):
    try: return await service.create(vehicle)
    except (VehicleAlreadyExistsError, UserNotFoundError) as exc: handle_error(exc)

@router.get("", response_model=list[VehicleResponse])
async def find_all_vehicles(service: VehicleService = Depends(get_vehicle_service), _admin=Depends(require_admin)):
    return await service.find_all()

@router.get("/user/{user_id}", response_model=list[VehicleResponse])
async def find_vehicles_by_user(user_id: str, service: VehicleService = Depends(get_vehicle_service), _admin=Depends(require_admin)):
    if not re.fullmatch(r"(?:[0-9a-fA-F]{24}|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})", user_id):
        raise HTTPException(status_code=422, detail="user_id debe ser un ObjectId o UUID válido")
    try: return await service.find_by_user(user_id)
    except UserNotFoundError as exc: handle_error(exc)

@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def find_vehicle_by_id(vehicle_id: str, service: VehicleService = Depends(get_vehicle_service), _admin=Depends(require_admin)):
    try: return await service.find_by_id(vehicle_id)
    except VehicleNotFoundError as exc: handle_error(exc)

@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(vehicle_id: str, data: VehicleUpdate, service: VehicleService = Depends(get_vehicle_service), _admin=Depends(require_admin)):
    try: return await service.update(vehicle_id, data)
    except (VehicleAlreadyExistsError, UserNotFoundError, VehicleNotFoundError, VehicleValidationError) as exc: handle_error(exc)

@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(vehicle_id: str, service: VehicleService = Depends(get_vehicle_service), _admin=Depends(require_admin)):
    try: await service.delete(vehicle_id)
    except VehicleNotFoundError as exc: handle_error(exc)
