from pydantic import BaseModel

from app.schemas.stroke import StrokePointSchema


class ClassifyWeightRequest(BaseModel):
    stroke_id: str
    points: list[StrokePointSchema]
