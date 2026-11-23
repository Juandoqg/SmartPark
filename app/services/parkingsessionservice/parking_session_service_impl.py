import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from pymongo.errors import DuplicateKeyError

from app.repositories.ports import RepositoryConflictError
from app.services.parkingsessionservice.parking_session_errors import ParkingSessionError
from app.services.parkingsessionservice.parking_session_service import ParkingSessionService


class ParkingSessionServiceImpl(ParkingSessionService):
    def __init__(self, space_repository, vehicle_repository, tariff_repository, session_repository, cache=None):
        self.space_repository = space_repository
        self.vehicle_repository = vehicle_repository
        self.tariff_repository = tariff_repository
        self.session_repository = session_repository
        self.cache = cache

    async def entry(self, data, user):
        values = data.model_dump()
        fingerprint = hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()
        existing = await self.session_repository.find_by_idempotency_key(user["id"], data.idempotency_key)
        if existing:
            if existing["request_fingerprint"] != fingerprint:
                raise ParkingSessionError("La clave de idempotencia ya se usó con otros datos", 409)
            return existing

        try:
            space = await self.space_repository.find_by_id(data.space_id)
            vehicle = await self.vehicle_repository.find_by_id(data.vehicle_id)
            tariff = await self.tariff_repository.find_by_id(data.tariff_id)
        except (ValueError, TypeError):
            space = vehicle = tariff = None
        if space is None or vehicle is None or tariff is None:
            raise ParkingSessionError("Espacio, vehículo o tarifa no encontrados", 404)
        if space["parking_id"] != data.parking_id:
            raise ParkingSessionError("El espacio no pertenece a la sede indicada", 422)
        if user.get("role") not in {"manager", "admin"} and vehicle["user_id"] != user["id"]:
            raise ParkingSessionError("El vehículo no pertenece al usuario", 403)
        if vehicle["vehicle_type"] not in space["allowed_vehicle_types"]:
            raise ParkingSessionError("El espacio no admite este tipo de vehículo", 409)
        if space["status"] != "available":
            raise ParkingSessionError("El espacio no está disponible", 409)
        if tariff["parking_id"] != data.parking_id or tariff["vehicle_type"] != vehicle["vehicle_type"] or not tariff["active"]:
            raise ParkingSessionError("La tarifa no está activa o no aplica a este vehículo y sede", 422)
        if await self.session_repository.find_active_by_vehicle(data.vehicle_id):
            raise ParkingSessionError("El vehículo ya tiene una sesión activa", 409)

        if self.cache and not await self.cache.acquire_space_lock(data.space_id, data.idempotency_key, 15):
            raise ParkingSessionError("Hay otra operación registrando este espacio; intenta de nuevo", 409)
        try:
            entry_at = datetime.now(timezone.utc)
            snapshot = {key: tariff[key] for key in
                        ("name", "vehicle_type", "currency", "hourly_rate", "reservation_rate", "billing_increment_minutes")}
            try:
                result = await self.session_repository.create_active({
                    "parking_id": data.parking_id, "space_id": data.space_id, "user_id": vehicle["user_id"],
                    "created_by": user["id"],
                    "vehicle_id": data.vehicle_id, "tariff_id": data.tariff_id,
                    "tariff_snapshot": snapshot, "entry_at": entry_at, "status": "active",
                    "payment_status": "pending", "idempotency_key": data.idempotency_key,
                    "request_fingerprint": fingerprint, "created_at": entry_at, "updated_at": entry_at,
                })
            except (RepositoryConflictError, DuplicateKeyError) as exc:
                # A concurrent retry using the same key should return the original session.
                existing = await self.session_repository.find_by_idempotency_key(user["id"], data.idempotency_key)
                if existing and existing.get("request_fingerprint") == fingerprint:
                    return existing
                raise ParkingSessionError(str(exc), 409) from exc
            if self.cache:
                await self.cache.invalidate_parking_spaces(data.parking_id)
            return result
        finally:
            if self.cache:
                await self.cache.release_space_lock(data.space_id, data.idempotency_key)

    async def exit(self, session_id, user):
        try:
            session = await self.session_repository.find_by_id(session_id)
        except (ValueError, TypeError):
            session = None
        if session is None:
            raise ParkingSessionError("Sesión no encontrada", 404)
        if user.get("role") not in {"manager", "admin"} and session["user_id"] != user["id"]:
            raise ParkingSessionError("No puedes cerrar la sesión de otro usuario", 403)
        if session["status"] != "active":
            raise ParkingSessionError("La sesión ya está cerrada", 409)

        exit_at = datetime.now(timezone.utc)
        entry_at = session["entry_at"]
        # Older Mongo records or alternate drivers may return naive UTC datetimes.
        if entry_at.tzinfo is None or entry_at.utcoffset() is None:
            entry_at = entry_at.replace(tzinfo=timezone.utc)
        else:
            entry_at = entry_at.astimezone(timezone.utc)
        elapsed_seconds = max(0, (exit_at - entry_at).total_seconds())
        duration_minutes = max(1, ceil(elapsed_seconds / 60))
        increment = session["tariff_snapshot"]["billing_increment_minutes"]
        billed_increments = ceil(duration_minutes / increment)
        hourly_rate = Decimal(str(session["tariff_snapshot"]["hourly_rate"]))
        total = (hourly_rate * billed_increments * Decimal(increment) / Decimal(60)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        try:
            completed = await self.session_repository.close_active(session_id, exit_at, duration_minutes, total)
        except (ValueError, TypeError):
            completed = None
        if completed is None:
            raise ParkingSessionError("La sesión ya fue cerrada", 409)
        if self.cache:
            await self.cache.invalidate_parking_spaces(session["parking_id"])
        return completed

    async def list_sessions(self, user, parking_id=None, status=None):
        is_manager = user.get("role") in {"manager", "admin"}
        return await self.session_repository.find(
            user_id=None if is_manager else user["id"], parking_id=parking_id, status=status,
        )
