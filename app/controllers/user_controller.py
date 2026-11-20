from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas.user_schema import UserCreate, UserResponse
from app.services.userservice.user_service import UserService
from app.services.userservice.user_service_impl import UserServiceImpl


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def get_user_service() -> UserService:
    return UserServiceImpl()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):

    try:
        return await service.create(user)

    except Exception as exception:
        from app.services.userservice.user_service_impl import UserAlreadyExistsError

        if isinstance(exception, UserAlreadyExistsError):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exception)
            )

        raise


@router.get(
    "",
    response_model=list[UserResponse]
)
async def find_all_users(
    service: UserService = Depends(get_user_service)
):

    return await service.find_all()