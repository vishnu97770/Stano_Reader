from fastapi import APIRouter, HTTPException

from app.schemas.analysis import StrokeAnalysisRequest
from recognizer.analyzer import analyze_stroke
from recognizer.schemas import StrokeFeatures

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze-stroke", response_model=StrokeFeatures)
def analyze_stroke_endpoint(body: StrokeAnalysisRequest) -> StrokeFeatures:
    if len(body.points) < 2:
        raise HTTPException(status_code=422, detail="A stroke must have at least 2 points")
    points = [p.model_dump() for p in body.points]
    return analyze_stroke(body.stroke_id, points)
