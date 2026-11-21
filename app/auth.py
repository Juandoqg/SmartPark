from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not subject:
            raise unauthorized
        user = await request.app.state.backend.user_repository.find_by_id(subject)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise unauthorized from None
    if user is None:
        raise unauthorized
    return user


def require_roles(*allowed_roles: str) -> Callable:
    async def role_guard(current_user=Depends(get_current_user)):
        if current_user.get("role", "user") not in allowed_roles:
            raise HTTPException(status_code=403, detail="No tienes permisos para esta operación")
        return current_user

    return role_guard


require_manager = require_roles("manager", "admin")
require_admin = require_roles("admin")
