from fastapi import APIRouter, HTTPException

from app.schemas.circle import ClassifyCircleRequest
from recognizer.analyzer import analyze_stroke
from recognizer.circle_detector import detect_circle
from recognizer.schemas import CircleResult

router = APIRouter(prefix="/api", tags=["circle"])


@router.post("/classify-circle", response_model=CircleResult)
def classify_circle_endpoint(body: ClassifyCircleRequest) -> CircleResult:
    if len(body.points) < 2:
        raise HTTPException(status_code=422, detail="A stroke must have at least 2 points")
    points = [p.model_dump() for p in body.points]
    features = analyze_stroke(body.stroke_id, points)
    return detect_circle(body.stroke_id, features, points)
