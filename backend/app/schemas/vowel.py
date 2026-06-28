from pydantic import BaseModel


class StrokePointSchema(BaseModel):
    x: float
    y: float
    pressure: float | None = None


class NearbyStrokeInfo(BaseModel):
    stroke_id: str
    family: str
    centroid_x: float
    centroid_y: float
    start_x: float
    start_y: float
    end_x: float
    end_y: float


class DetectVowelRequest(BaseModel):
    stroke_id: str
    points: list[StrokePointSchema]
    nearby_strokes: list[NearbyStrokeInfo] = []
