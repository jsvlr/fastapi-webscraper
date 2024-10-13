from fastapi import APIRouter
from app.api.v1.weather import router as weather_router
from app.api.v1.manga import router as manga_router


router = APIRouter()
router.include_router(weather_router, prefix="/weather", tags=["weather"])
router.include_router(manga_router, prefix="/manga", tags=["manga"])