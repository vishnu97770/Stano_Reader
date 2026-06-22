from fastapi import APIRouter

from app.api.sessions import router as sessions_router

api_router = APIRouter()
api_router.include_router(sessions_router)
