from pydantic import BaseModel, Field

from app.schemas.stroke import StrokePointSchema


class ClassifyPositionRequest(BaseModel):
    stroke_id: str
    points: list[StrokePointSchema]
    canvas_height: float = Field(gt=0, description="Visible canvas height in CSS pixels")
    baseline_mode: str = "VIRTUAL"   # reserved for future: "PITMAN_RULED", "SCANNED", "CUSTOM"
