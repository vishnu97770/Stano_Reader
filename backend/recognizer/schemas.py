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


class PressureStats(BaseModel):
    avg_pressure: float    # mean pressure across all sampled points, in [0, 1]
    max_pressure: float    # peak pressure observed during the stroke
    variance: float        # pressure variance (0 = constant, higher = variable)
    sample_count: int      # number of points that contributed pressure data


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
    # M7 — None when input points carry no pressure key (fallback to frequency priors)
    pressure_stats: PressureStats | None = None


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


# ---------------------------------------------------------------------------
# M13A — Circle and loop detection schemas
# ---------------------------------------------------------------------------

class CircleResult(BaseModel):
    stroke_id: str
    is_circle: bool
    circle_type: str | None    # "SMALL_CIRCLE" | "LARGE_CIRCLE" | "SMALL_LOOP" | "LARGE_LOOP"
    phoneme: str | None        # IPA phoneme; None when is_circle = False
    confidence: float          # [0, 1]; 0.0 when is_circle = False
    position: str              # "ANY" now; future: "INITIAL" | "MEDIAL" | "FINAL"
    reasoning: str | None      # human-readable; None when is_circle = False


# ---------------------------------------------------------------------------
# M7 — Stroke weight (pressure) classification schemas
# ---------------------------------------------------------------------------

class WeightResult(BaseModel):
    stroke_id: str
    weight: str             # "LIGHT" | "HEAVY" | "AMBIGUOUS"
    avg_pressure: float
    max_pressure: float
    variance: float
    threshold_light: float  # pressure at or below which a stroke is LIGHT
    threshold_heavy: float  # pressure at or above which a stroke is HEAVY
