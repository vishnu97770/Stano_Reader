from pydantic import BaseModel

from app.schemas.stroke import StrokePointSchema


class ClassifyHookRequest(BaseModel):
    stroke_id: str
    points: list[StrokePointSchema]
