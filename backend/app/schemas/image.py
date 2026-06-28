from pydantic import BaseModel


class ImageStrokePointSchema(BaseModel):
    x: float
    y: float
    pressure: float = 0.5
    timestamp: int = 0


class ImageStrokeSchema(BaseModel):
    id: str
    points: list[ImageStrokePointSchema]


class ImageProcessRequest(BaseModel):
    strokes: list[ImageStrokeSchema]
    canvas_height: float = 600.0   # from PageMetadata.canvas_height
    canvas_width: float = 800.0
