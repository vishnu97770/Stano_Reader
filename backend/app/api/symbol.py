from fastapi import APIRouter, HTTPException

from app.schemas.symbol import ClassifySymbolRequest
from recognizer.schemas import SymbolResult
from recognizer.symbol_classifier import classify_symbol_from_points

router = APIRouter(prefix="/api", tags=["symbol"])


@router.post("/classify-symbol", response_model=SymbolResult)
def classify_symbol_endpoint(body: ClassifySymbolRequest) -> SymbolResult:
    if len(body.points) < 2:
        raise HTTPException(status_code=422, detail="A stroke must have at least 2 points")
    points = [p.model_dump() for p in body.points]
    return classify_symbol_from_points(body.stroke_id, points)
