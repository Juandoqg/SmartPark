from fastapi import APIRouter, HTTPException, status

from app.schemas.user_schema import UserCreate, UserResponse
from app.services.user_service import (
    UserService,
    UserAlreadyExistsError
)


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_user(user: UserCreate):

    try:
        return await UserService.create(user)

    except UserAlreadyExistsError as exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exception)
        )


@router.get(
    "",
    response_model=list[UserResponse]
)
async def find_all_users():

    return await UserService.find_all()