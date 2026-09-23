from fastapi import APIRouter

from app.api.v1 import models, battles

api_router = APIRouter()

api_router.include_router(models.router, prefix="/models", tags=["Models"])
api_router.include_router(battles.router, prefix="/battles", tags=["Battles"])
