from pydantic import BaseModel


class BoundingBox(BaseModel):
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    width: float
    height: float


class StrokeFeatures(BaseModel):
    stroke_id: str
    length: float               # total path length (px)
    avg_segment_length: float   # avg dist between consecutive points (px)
    direction: str              # dominant direction label (e.g. "down-right")
    angle: float                # start-to-end angle in degrees, [0, 360)
    bounding_box: BoundingBox
    point_count: int
    avg_point_distance: float   # alias of avg_segment_length, exposed for clarity
    is_curve: bool
    curvature_ratio: float      # path_length / chord_length
