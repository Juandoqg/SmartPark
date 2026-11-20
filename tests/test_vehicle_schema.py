import pytest
from pydantic import ValidationError
from app.schemas.vehicle_schema import VehicleCreate


def test_vehicle_normalizes_plate_and_type():
    vehicle = VehicleCreate(plate="abc 123", vehicle_type="Carro", user_id="507f1f77bcf86cd799439011")
    assert vehicle.plate == "ABC123"
    assert vehicle.vehicle_type == "carro"


def test_vehicle_accepts_postgres_uuid_user_id():
    vehicle = VehicleCreate(
        plate="MPD89D",
        vehicle_type="bicicleta",
        user_id="e5d8a4fb-80b6-4617-914e-571f7edc2d37",
    )
    assert vehicle.user_id == "e5d8a4fb-80b6-4617-914e-571f7edc2d37"


def test_vehicle_update_accepts_mongo_object_id():
    update = VehicleUpdate(user_id="507f1f77bcf86cd799439011")
    assert update.user_id == "507f1f77bcf86cd799439011"


def test_bicycle_can_be_created_without_plate():
    vehicle = VehicleCreate(
        vehicle_type="bicicleta",
        user_id="e5d8a4fb-80b6-4617-914e-571f7edc2d37",
    )
    assert vehicle.plate is None


@pytest.mark.parametrize("vehicle_type", ["carro", "moto"])
def test_motor_vehicle_requires_plate(vehicle_type):
    with pytest.raises(ValidationError):
        VehicleCreate(vehicle_type=vehicle_type, user_id="e5d8a4fb-80b6-4617-914e-571f7edc2d37")


def test_only_car_moto_and_bicycle_are_allowed():
    with pytest.raises(ValidationError):
        VehicleCreate(plate="ABC123", vehicle_type="camioneta", user_id="e5d8a4fb-80b6-4617-914e-571f7edc2d37")


@pytest.mark.parametrize("payload", [
    {"plate": "A!", "vehicle_type": "carro", "user_id": "507f1f77bcf86cd799439011"},
    {"plate": "ABC123", "vehicle_type": "avion", "user_id": "507f1f77bcf86cd799439011"},
    {"plate": "ABC123", "vehicle_type": "carro", "user_id": "no-es-objectid"},
])
def test_vehicle_rejects_invalid_values(payload):
    with pytest.raises(ValidationError):
        VehicleCreate(**payload)
