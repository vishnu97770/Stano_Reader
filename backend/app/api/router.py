from fastapi import APIRouter

from app.api.analysis import router as analysis_router
from app.api.candidate import router as candidate_router
from app.api.circle import router as circle_router
from app.api.classify import router as classify_router
from app.api.hook import router as hook_router
from app.api.length import router as length_router
from app.api.phrase import router as phrase_router
from app.api.position import router as position_router
from app.api.phoneme import router as phoneme_router
from app.api.sessions import router as sessions_router
from app.api.symbol import router as symbol_router
from app.api.weight import router as weight_router

api_router = APIRouter()
api_router.include_router(sessions_router)
api_router.include_router(analysis_router)
api_router.include_router(classify_router)
api_router.include_router(symbol_router)
api_router.include_router(weight_router)
api_router.include_router(phoneme_router)
api_router.include_router(candidate_router)
api_router.include_router(circle_router)
api_router.include_router(hook_router)
api_router.include_router(length_router)
api_router.include_router(phrase_router)
api_router.include_router(position_router)
