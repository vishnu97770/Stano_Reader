import json
from datetime import datetime

from pydantic import BaseModel, field_validator


class StrokePointSchema(BaseModel):
    x: float
    y: float
    pressure: float = 0.5   # [0, 1]; mouse default per W3C spec; absent in pre-M7 data
    timestamp: int


class StrokeCreate(BaseModel):
    id: str
    points: list[StrokePointSchema]
    pen_color: str = "#1a1a1a"
    pen_width: float = 2.5


class StrokeResponse(BaseModel):
    id: str
    session_id: str
    points: list[StrokePointSchema]
    pen_color: str
    pen_width: float
    created_at: datetime

    @field_validator("points", mode="before")
    @classmethod
    def deserialize_points(cls, v: str | list) -> list:
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = {"from_attributes": True}


class StrokesBulkCreate(BaseModel):
    strokes: list[StrokeCreate]


class StrokesSavedResponse(BaseModel):
    saved: int
