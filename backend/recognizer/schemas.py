from pydantic import BaseModel


# ---------------------------------------------------------------------------
# M4 — Feature extraction schemas
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# M5 — Family classification schemas
# ---------------------------------------------------------------------------

class FamilyMatch(BaseModel):
    family: str       # e.g. "TD_FAMILY"
    confidence: float # [0, 1] — how well the stroke matches this family


class FamilyResult(BaseModel):
    stroke_id: str
    family: str                         # best-matching family, or "UNKNOWN"
    confidence: float                   # score of the best match
    alternatives: list[FamilyMatch]     # other families above noise floor, sorted desc


# ---------------------------------------------------------------------------
# M6 — Exact symbol classification schemas
# ---------------------------------------------------------------------------

class SymbolMatch(BaseModel):
    symbol: str
    confidence: float   # [0, 1]


class SymbolResult(BaseModel):
    stroke_id: str
    family: str                         # inherited from FamilyResult
    family_confidence: float            # family-level confidence (for display context)
    symbol: str                         # best-matching symbol, or "UNKNOWN"
    confidence: float                   # symbol-level confidence
    alternatives: list[SymbolMatch]     # other symbols above noise floor, sorted desc
    thickness_missing: bool             # True when voiced/unvoiced required pressure data
    reason: str | None                  # human-readable explanation of any limitation
