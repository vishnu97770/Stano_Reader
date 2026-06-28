from fastapi import APIRouter, HTTPException

from app.schemas.length import ClassifyLengthRequest
from recognizer.analyzer import analyze_stroke
from recognizer.length_detector import detect_length
from recognizer.schemas import LengthResult

router = APIRouter(prefix="/api", tags=["length"])


@router.post("/classify-length", response_model=LengthResult)
def classify_length_endpoint(body: ClassifyLengthRequest) -> LengthResult:
    if len(body.points) < 2:
        raise HTTPException(status_code=422, detail="A stroke must have at least 2 points")
    points = [p.model_dump() for p in body.points]
    features = analyze_stroke(body.stroke_id, points)
    return detect_length(body.stroke_id, features, body.family_name)
