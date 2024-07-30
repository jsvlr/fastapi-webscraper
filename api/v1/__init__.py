from fastapi import APIRouter
from app.api.v1 import weather

router = APIRouter()
router.include_router(weather.router, prefix="/weather", tags=["weather"])