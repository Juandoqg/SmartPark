import pytest
from pydantic import ValidationError

from app.schemas.parking_schema import ParkingCreate, ParkingUpdate


def valid_parking(**overrides):
    data = {
        "name": "  SmartPark   Centro ",
        "address": " Calle 10 # 20-30 ",
        "city": "medellin",
        "zones": [
            {"name": "  Nivel   1 ", "description": " Zona cubierta "},
            {"name": "Motos"},
        ],
    }
    data.update(overrides)
    return ParkingCreate(**data)


def test_parking_normalizes_fields_and_zones():
    parking = valid_parking()
    assert parking.name == "SmartPark Centro"
    assert parking.address == "Calle 10 # 20-30"
    assert parking.city == "Medellin"
    assert parking.zones[0].name == "Nivel 1"
    assert parking.zones[0].description == "Zona cubierta"


@pytest.mark.parametrize("overrides", [
    {"name": "  "},
    {"address": "abc"},
    {"city": "1"},
    {"city": "$$$"},
    {"zones": []},
    {"zones": [{"name": "Norte"}, {"name": " norte "}]},
    {"zones": [{"name": "!@#$"}]},
    {"unknown": "field"},
])
def test_parking_rejects_invalid_data(overrides):
    with pytest.raises(ValidationError):
        valid_parking(**overrides)


def test_parking_update_accepts_partial_fields():
    update = ParkingUpdate(city="bogota")
    assert update.city == "Bogota"


@pytest.mark.parametrize("payload", [{}, {"name": None}, {"zones": None}, {"new_field": "x"}])
def test_parking_update_rejects_empty_null_or_unknown_fields(payload):
    with pytest.raises(ValidationError):
        ParkingUpdate(**payload)
