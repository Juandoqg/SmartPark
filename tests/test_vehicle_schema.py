import pytest
from pydantic import ValidationError
from app.schemas.vehicle_schema import VehicleCreate


def test_vehicle_normalizes_plate_and_type():
    vehicle = VehicleCreate(plate="abc 123", vehicle_type="Carro", user_id="507f1f77bcf86cd799439011")
    assert vehicle.plate == "ABC123"
    assert vehicle.vehicle_type == "carro"


@pytest.mark.parametrize("payload", [
    {"plate": "A!", "vehicle_type": "carro", "user_id": "507f1f77bcf86cd799439011"},
    {"plate": "ABC123", "vehicle_type": "avion", "user_id": "507f1f77bcf86cd799439011"},
    {"plate": "ABC123", "vehicle_type": "carro", "user_id": "no-es-objectid"},
])
def test_vehicle_rejects_invalid_values(payload):
    with pytest.raises(ValidationError):
        VehicleCreate(**payload)
