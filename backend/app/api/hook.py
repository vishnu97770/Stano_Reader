from fastapi import APIRouter, HTTPException

from app.schemas.hook import ClassifyHookRequest
from recognizer.analyzer import analyze_stroke
from recognizer.hook_detector import detect_hook
from recognizer.schemas import HookResult

router = APIRouter(prefix="/api", tags=["hook"])


@router.post("/classify-hook", response_model=HookResult)
def classify_hook_endpoint(body: ClassifyHookRequest) -> HookResult:
    if len(body.points) < 2:
        raise HTTPException(status_code=422, detail="A stroke must have at least 2 points")
    points = [p.model_dump() for p in body.points]
    features = analyze_stroke(body.stroke_id, points)
    return detect_hook(body.stroke_id, features, points)
