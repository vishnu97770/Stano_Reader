from fastapi import APIRouter, HTTPException

from app.schemas.vowel import DetectVowelRequest
from recognizer.schemas import VowelResult
from recognizer.vowel_detector import detect_vowel

router = APIRouter(prefix="/api", tags=["vowel"])


@router.post("/detect-vowel", response_model=VowelResult)
def detect_vowel_endpoint(body: DetectVowelRequest) -> VowelResult:
    if len(body.points) < 1:
        raise HTTPException(
            status_code=422,
            detail="A stroke must have at least 1 point",
        )
    nearby = [s.model_dump() for s in body.nearby_strokes]
    points = [{"x": p.x, "y": p.y} for p in body.points]
    return detect_vowel(body.stroke_id, points, nearby)
