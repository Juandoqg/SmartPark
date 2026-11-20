import pytest
from pydantic import ValidationError
from app.schemas.user_schema import UserCreate


def test_user_create_normalizes_name_email_and_phone():
    user = UserCreate(full_name="  Ana   María Pérez ", email="ANA@EXAMPLE.COM", phone="+57 300 1234567")
    assert user.full_name == "Ana María Pérez"
    assert user.email == "ana@example.com"
    assert user.phone == "+57 300 1234567"


@pytest.mark.parametrize("payload", [
    {"full_name": "Jo", "email": "ana@example.com"},
    {"full_name": "123", "email": "ana@example.com"},
    {"full_name": "Ana Pérez", "email": "no-es-correo"},
    {"full_name": "Ana Pérez", "email": "ana@example.com", "phone": "abc1234567"},
    {"full_name": "Ana Pérez", "email": "ana@example.com", "unexpected": True},
])
def test_user_create_rejects_invalid_input(payload):
    with pytest.raises(ValidationError):
        UserCreate(**payload)


def test_phone_is_optional():
    assert UserCreate(full_name="Ana Pérez", email="ana@example.com").phone is None
