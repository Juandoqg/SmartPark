import json
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Best-effort Redis cache; MongoDB/PostgreSQL remain the source of truth."""

    def __init__(self, client):
        self.client = client

    @classmethod
    async def connect(cls):
        from redis.asyncio import Redis

        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        return cls(client)

    async def get_json(self, key: str):
        try:
            value = await self.client.get(key)
            return json.loads(value) if value is not None else None
        except Exception:
            logger.exception("Redis cache read failed for %s", key)
            return None

    async def set_json(self, key: str, value, ttl_seconds: int):
        try:
            await self.client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
        except Exception:
            logger.exception("Redis cache write failed for %s", key)

    async def invalidate_parking_spaces(self, parking_id: str):
        try:
            keys = [key async for key in self.client.scan_iter(match=f"smartpark:availability:{parking_id}:*")]
            if keys:
                await self.client.delete(*keys)
        except Exception:
            logger.exception("Redis cache invalidation failed for parking %s", parking_id)

    async def acquire_space_lock(self, space_id: str, operation_id: str, ttl_seconds: int) -> bool:
        """Acquire an expiring space lock without overwriting another operation's lock."""
        try:
            return bool(await self.client.set(
                f"smartpark:space-lock:{space_id}", operation_id, ex=ttl_seconds, nx=True
            ))
        except Exception:
            logger.exception("Redis reservation lock failed for space %s", space_id)
            return False

    async def release_space_lock(self, space_id: str, operation_id: str):
        """Release only the lock owned by this operation."""
        try:
            await self.client.eval(
                "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end",
                1, f"smartpark:space-lock:{space_id}", operation_id,
            )
        except Exception:
            logger.exception("Redis reservation lock release failed for space %s", space_id)

    async def close(self):
        await self.client.aclose()
