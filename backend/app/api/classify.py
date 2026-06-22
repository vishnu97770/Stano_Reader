from fastapi import APIRouter, HTTPException

from app.schemas.classify import ClassifyFamilyRequest
from recognizer.family_classifier import classify_from_points
from recognizer.schemas import FamilyResult

router = APIRouter(prefix="/api", tags=["classification"])


@router.post("/classify-family", response_model=FamilyResult)
def classify_family_endpoint(body: ClassifyFamilyRequest) -> FamilyResult:
    if len(body.points) < 2:
        raise HTTPException(status_code=422, detail="A stroke must have at least 2 points")
    points = [p.model_dump() for p in body.points]
    return classify_from_points(body.stroke_id, points)
