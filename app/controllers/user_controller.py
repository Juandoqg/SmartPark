from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import require_admin
from app.dependencies import get_user_service
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from app.services.userservice.user_service import UserService
from app.services.userservice.user_errors import UserAlreadyExistsError, UserHasVehiclesError, UserNotFoundError

router = APIRouter(prefix="/users", tags=["Users"])

def _handle_error(exception):
    if isinstance(exception, UserAlreadyExistsError):
        raise HTTPException(status_code=409, detail=str(exception)) from exception
    if isinstance(exception, UserHasVehiclesError):
        raise HTTPException(status_code=409, detail=str(exception)) from exception
    if isinstance(exception, UserNotFoundError):
        raise HTTPException(status_code=404, detail=str(exception)) from exception

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, service: UserService = Depends(get_user_service)):
    try: return await service.create(user)
    except UserAlreadyExistsError as exc: _handle_error(exc)

@router.get("", response_model=list[UserResponse])
async def find_all_users(service: UserService = Depends(get_user_service), _admin=Depends(require_admin)):
    return await service.find_all()

@router.get("/by-email/{email}", response_model=UserResponse)
async def find_user_by_email(email: str, service: UserService = Depends(get_user_service), _admin=Depends(require_admin)):
    user = await service.find_by_email(email)
    if user is None: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.get("/{user_id}", response_model=UserResponse)
async def find_user_by_id(user_id: str, service: UserService = Depends(get_user_service), _admin=Depends(require_admin)):
    try: return await service.find_by_id(user_id)
    except UserNotFoundError as exc: _handle_error(exc)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, data: UserUpdate, service: UserService = Depends(get_user_service), _admin=Depends(require_admin)):
    try: return await service.update(user_id, data)
    except (UserAlreadyExistsError, UserNotFoundError) as exc: _handle_error(exc)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, service: UserService = Depends(get_user_service), _admin=Depends(require_admin)):
    try:
        await service.delete(user_id)
    except (UserNotFoundError, UserHasVehiclesError) as exc: _handle_error(exc)
