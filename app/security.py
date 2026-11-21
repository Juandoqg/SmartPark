from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config.settings import settings

password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hash.hash("smartpark-invalid-login-placeholder")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        # Keep unknown-email and legacy-account checks close to the normal Argon2 cost.
        hashed_password = DUMMY_PASSWORD_HASH
    try:
        return password_hash.verify(password, hashed_password)
    except Exception:
        return False


def create_access_token(subject: str, role: str, email: str, phone: str) -> str:
    if len(settings.JWT_SECRET_KEY) < 32 or settings.JWT_SECRET_KEY.startswith("replace-with-"):
        raise RuntimeError("JWT_SECRET_KEY debe tener al menos 32 caracteres")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "email": email,
        "phone": phone,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
