from fastapi import APIRouter, HTTPException

from app.schemas.position import ClassifyPositionRequest
from recognizer.position_detector import detect_position
from recognizer.schemas import PositionResult

router = APIRouter(prefix="/api", tags=["position"])


@router.post("/classify-position", response_model=PositionResult)
def classify_position_endpoint(body: ClassifyPositionRequest) -> PositionResult:
    if len(body.points) < 2:
        raise HTTPException(status_code=422, detail="A stroke must have at least 2 points")
    points = [p.model_dump() for p in body.points]
    return detect_position(body.stroke_id, points, body.canvas_height, body.baseline_mode)
