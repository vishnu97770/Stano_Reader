from fastapi import APIRouter, HTTPException

from app.schemas.weight import ClassifyWeightRequest
from recognizer.schemas import WeightResult
from recognizer.weight_classifier import classify_weight

router = APIRouter(prefix="/api", tags=["weight"])


@router.post("/classify-weight", response_model=WeightResult)
def classify_weight_endpoint(body: ClassifyWeightRequest) -> WeightResult:
    if len(body.points) < 2:
        raise HTTPException(status_code=422, detail="A stroke must have at least 2 points")
    points = [p.model_dump() for p in body.points]
    return classify_weight(body.stroke_id, points)
