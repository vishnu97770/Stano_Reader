from pydantic import BaseModel

from app.schemas.stroke import StrokePointSchema


class ClassifyLengthRequest(BaseModel):
    stroke_id: str
    points: list[StrokePointSchema]
    family_name: str | None = None   # optional; supply from classify-symbol result
