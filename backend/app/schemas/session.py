from datetime import datetime

from pydantic import BaseModel

from app.schemas.stroke import StrokeResponse


class SessionCreate(BaseModel):
    name: str = ""


class SessionSummary(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    stroke_count: int


class SessionDetail(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    strokes: list[StrokeResponse]
    transcript: list[str] = []
