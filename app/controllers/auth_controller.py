from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from app.config.settings import settings

from app.auth import get_current_user
from app.security import create_access_token, verify_password
from app.schemas.user_schema import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    user = await request.app.state.backend.user_repository.find_by_email(form.username.strip().lower())
    is_valid = await run_in_threadpool(
        verify_password, form.password, user.get("password_hash") if user else None
    )
    if not user or not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.get("phone"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta no tiene teléfono registrado. Un administrador debe actualizar el perfil.",
        )
    token = create_access_token(
        str(user["id"]),
        user.get("role", "user"),
        str(user["email"]),
        user["phone"],
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return current_user
