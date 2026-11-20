from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config.settings import settings
from app.database.mongodb import MongoDB
from app.controllers.user_controller import router as user_router
from app.controllers.vehicle_controller import router as vehicle_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await MongoDB.connect()
    yield
    await MongoDB.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="SmartPark - Sistema inteligente de gestión de parqueaderos",
    lifespan=lifespan,
)
app.include_router(user_router, prefix=settings.API_V1_PREFIX)
app.include_router(vehicle_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "UP", "application": settings.APP_NAME, "version": settings.APP_VERSION}
