from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config.settings import settings
from app.database.backend import create_backend
from app.controllers.user_controller import router as user_router
from app.controllers.vehicle_controller import router as vehicle_router
from app.controllers.parking_controller import router as parking_router
from app.controllers.parking_space_controller import router as parking_space_router
from app.database.redis_cache import RedisCache


@asynccontextmanager
async def lifespan(app: FastAPI):
    backend = create_backend()
    await backend.connect()
    app.state.backend = backend
    app.state.redis_cache = None
    try:
        if settings.REDIS_ENABLED:
            app.state.redis_cache = await RedisCache.connect()
        yield
    finally:
        try:
            if app.state.redis_cache is not None:
                await app.state.redis_cache.close()
        finally:
            await backend.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="SmartPark - Sistema inteligente de gestión de parqueaderos",
    lifespan=lifespan,
)
app.include_router(user_router, prefix=settings.API_V1_PREFIX)
app.include_router(vehicle_router, prefix=settings.API_V1_PREFIX)
app.include_router(parking_router, prefix=settings.API_V1_PREFIX)
app.include_router(parking_space_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "UP", "application": settings.APP_NAME, "version": settings.APP_VERSION}
