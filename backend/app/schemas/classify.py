from pydantic import BaseModel

from app.schemas.stroke import StrokePointSchema


class ClassifyFamilyRequest(BaseModel):
    stroke_id: str
    points: list[StrokePointSchema]
