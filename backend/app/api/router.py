from fastapi import APIRouter

from app.api.analysis import router as analysis_router
from app.api.classify import router as classify_router
from app.api.sessions import router as sessions_router

api_router = APIRouter()
api_router.include_router(sessions_router)
api_router.include_router(analysis_router)
api_router.include_router(classify_router)
