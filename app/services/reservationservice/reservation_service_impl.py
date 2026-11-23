import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from math import ceil
from app.repositories.ports import RepositoryConflictError
from app.services.reservationservice.reservation_service import ReservationService
from app.services.reservationservice.reservation_errors import ReservationError


class ReservationServiceImpl(ReservationService):
    def __init__(self, space_repository, vehicle_repository, tariff_repository, reservation_repository, cache=None):
        self.space_repository = space_repository
        self.vehicle_repository = vehicle_repository
        self.tariff_repository = tariff_repository
        self.reservation_repository = reservation_repository
        self.cache = cache

    async def create(self, data, user):
        values = data.model_dump()
        fingerprint = hashlib.sha256(json.dumps({k: str(v) for k, v in values.items() if k != "idempotency_key"}, sort_keys=True).encode()).hexdigest()
        existing = await self.reservation_repository.find_by_idempotency_key(user["id"], data.idempotency_key)
        if existing:
            if existing.get("request_fingerprint") != fingerprint:
                raise ReservationError("La clave de idempotencia ya se usó con otros datos", 409)
            return existing
        try:
            space = await self.space_repository.find_by_id(data.space_id)
            vehicle = await self.vehicle_repository.find_by_id(data.vehicle_id)
            tariff = await self.tariff_repository.find_by_id(data.tariff_id)
        except (ValueError, TypeError):
            space = vehicle = tariff = None
        if space is None or vehicle is None or tariff is None:
            raise ReservationError("Espacio, vehículo o tarifa no encontrados", 404)
        if vehicle["user_id"] != user["id"]:
            raise ReservationError("El vehículo no pertenece al usuario", 403)
        if space["status"] != "available" or vehicle["vehicle_type"] not in space["allowed_vehicle_types"]:
            raise ReservationError("El espacio no admite el vehículo o no está disponible", 409)
        if tariff["parking_id"] != space["parking_id"] or tariff["vehicle_type"] != vehicle["vehicle_type"] or not tariff["active"]:
            raise ReservationError("La tarifa no aplica a este espacio y vehículo", 422)
        if await self.reservation_repository.has_overlap(data.space_id, data.starts_at, data.ends_at):
            raise ReservationError("El espacio ya está reservado en ese horario", 409)
        if self.cache and not await self.cache.acquire_space_lock(data.space_id, data.idempotency_key, 15):
            raise ReservationError("Hay otra operación reservando este espacio; intenta de nuevo", 409)
        try:
            duration = (data.ends_at - data.starts_at).total_seconds() / 60
            increments = ceil(duration / tariff["billing_increment_minutes"])
            total = Decimal(str(tariff["reservation_rate"])) + Decimal(str(tariff["hourly_rate"])) * increments * Decimal(tariff["billing_increment_minutes"]) / Decimal(60)
            try:
                return await self.reservation_repository.create({
                    "parking_id": space["parking_id"], "space_id": data.space_id, "user_id": user["id"],
                    "vehicle_id": data.vehicle_id, "tariff_id": data.tariff_id,
                    "tariff_snapshot": {k: tariff[k] for k in ("name", "vehicle_type", "currency", "hourly_rate", "reservation_rate", "billing_increment_minutes")},
                    "estimated_total": total, "starts_at": data.starts_at, "ends_at": data.ends_at,
                    "status": "confirmed", "idempotency_key": data.idempotency_key,
                    "request_fingerprint": fingerprint, "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                })
            except RepositoryConflictError as exc:
                raise ReservationError(str(exc), 409) from exc
        finally:
            if self.cache:
                await self.cache.release_space_lock(data.space_id, data.idempotency_key)

    async def list_mine(self, user):
        return await self.reservation_repository.find_by_user(user["id"])

    async def cancel(self, reservation_id, user):
        try:
            result = await self.reservation_repository.cancel(reservation_id, user["id"])
        except (ValueError, TypeError):
            result = None
        if result is None:
            raise ReservationError("Reserva no encontrada o ya cancelada", 404)
        return result
