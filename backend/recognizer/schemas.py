from typing import Annotated

from pydantic import BaseModel, model_validator
from pydantic.functional_validators import BeforeValidator


# ---------------------------------------------------------------------------
# Shared coercion — used by M13A/B/C result types whose detector code
# passes reasoning=None on the "not detected" path.  Converts None → ""
# so all result types expose reasoning: str with no nulls anywhere.
# ---------------------------------------------------------------------------

def _coerce_none_to_empty(v: object) -> str:
    return v if isinstance(v, str) else ("" if v is None else str(v))

_ReasoningStr = Annotated[str, BeforeValidator(_coerce_none_to_empty)]


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
    reasoning: str = ""                 # M14 — human-readable explanation; "" when UNKNOWN


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
    reasoning: str = ""                 # M14 — renamed from "reason"; "" when unavailable

    @model_validator(mode="before")
    @classmethod
    def _migrate_reason_field(cls, data: object) -> object:
        # symbol_classifier.py still passes reason= (old name); map it here
        # so the detector file needs no change.
        if isinstance(data, dict):
            data = dict(data)
            if "reason" in data and "reasoning" not in data:
                data["reasoning"] = data.pop("reason") or ""
            if data.get("reasoning") is None:
                data["reasoning"] = ""
        return data


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
    detected: bool = True   # M14 — False when no pressure data; True for all real classifications
    confidence: float = 0.0 # M14 — confidence in the weight classification; 0.0 = not computed
    reasoning: str = ""     # M14 — human-readable explanation; "" until weight engine sets it


# ---------------------------------------------------------------------------
# M13A — Circle and loop detection schemas
# ---------------------------------------------------------------------------

class CircleResult(BaseModel):
    stroke_id: str
    is_circle: bool
    circle_type: str | None    # "SMALL_CIRCLE" | "LARGE_CIRCLE" | "SMALL_LOOP" | "LARGE_LOOP"
    phoneme: str | None        # IPA phoneme; None when is_circle = False
    confidence: float          # [0, 1]; 0.0 when is_circle = False
    alternatives: list = []    # M14 — placeholder; future: ranked alternative circle types
    word_position: str         # "ANY" now; future: "INITIAL" | "MEDIAL" | "FINAL"
    reasoning: _ReasoningStr = ""  # M14 — "" when is_circle = False (was: str | None)


# ---------------------------------------------------------------------------
# M13B — Hook detection schemas
# ---------------------------------------------------------------------------

class HookResult(BaseModel):
    stroke_id: str
    is_hook: bool
    hook_type: str | None         # "L_HOOK_INITIAL" | "R_HOOK_INITIAL" | "N_HOOK_FINAL" | "FV_HOOK_FINAL"
    attachment_position: str | None  # "INITIAL" | "FINAL"; None when is_hook = False
    phoneme: str | None           # IPA phoneme; None when is_hook = False
    confidence: float             # [0, 1]; 0.0 when is_hook = False
    alternatives: list = []       # M14 — placeholder; future: ranked alternative hook types
    reasoning: _ReasoningStr = ""  # M14 — "" when is_hook = False (was: str | None)


# ---------------------------------------------------------------------------
# M13C — Halving and doubling detection schemas
# ---------------------------------------------------------------------------

class LengthResult(BaseModel):
    stroke_id: str
    is_modified: bool
    modification_type: str | None   # "HALF" | "DOUBLE"; None when is_modified = False
    added_phoneme: str | None       # IPA phoneme appended by the modification
    confidence: float               # [0, 1]; 0.0 when is_modified = False
    alternatives: list = []         # M14 — placeholder; future: ranked alternative modifications
    canonical_length: float         # reference length used (px)
    measured_length: float          # actual stroke path length (px)
    length_ratio: float             # measured_length / canonical_length
    reasoning: _ReasoningStr = ""   # M14 — "" when is_modified = False (was: str | None)


# ---------------------------------------------------------------------------
# M15 — Phraseography detection schemas
# ---------------------------------------------------------------------------

class PhraseMatch(BaseModel):
    phrase_text: str    # alternative phrase that also matched the outline
    confidence: float   # [0, 1]


class PhraseResult(BaseModel):
    stroke_id: str
    is_phrase: bool
    phrase_text: str | None             # matched phrase; None when is_phrase=False
    confidence: float                   # [0, 1]; 0.0 when is_phrase=False
    alternatives: list[PhraseMatch] = [] # other phrases that matched the same outline
    reasoning: str = ""                 # always populated


# ---------------------------------------------------------------------------
# M15.5 — Vowel sign detection schemas
# ---------------------------------------------------------------------------

class VowelResult(BaseModel):
    stroke_id: str
    is_vowel: bool
    vowel_symbol: str | None         # e.g. "DOT2_BEFORE"; None when is_vowel=False
    ipa: str | None                  # IPA phoneme string; None when is_vowel=False
    degree: int | None               # 1, 2, or 3; None when is_vowel=False
    position: str | None             # "before" | "after"; None when is_vowel=False
    attached_to_stroke_id: str | None  # consonant stroke this vowel attaches to
    detected: bool = False           # M14 standard; True only when is_vowel=True
    confidence: float = 0.0          # [0, 1]; 0.0 when is_vowel=False
    reasoning: str = ""              # always populated by detector
    alternatives: list = []          # M14 standard placeholder


# ---------------------------------------------------------------------------
# M16 — Image upload and processing schemas
# ---------------------------------------------------------------------------

class ExtractedStrokePoint(BaseModel):
    x: float
    y: float
    pressure: float = 0.5   # always 0.5 for image-extracted strokes (no stylus data)
    timestamp: int = 0


class ExtractedStroke(BaseModel):
    id: str
    points: list[ExtractedStrokePoint]


class WritingZone(BaseModel):
    top: float      # y-coordinate of first inked row in the zone
    bottom: float   # y-coordinate of last inked row
    baseline: float # estimated baseline y


class PageMetadata(BaseModel):
    canvas_width: float     # normalised canvas width (= image_processor.TARGET_WIDTH)
    canvas_height: float    # normalised canvas height; passed to detect_position
    writing_zones: list[WritingZone]
    line_count: int
    image_width: int        # actual width of preprocessed image in pixels
    image_height: int       # actual height of preprocessed image in pixels


class ImageUploadResult(BaseModel):
    strokes: list[ExtractedStroke]
    stroke_count: int
    page_metadata: PageMetadata


class ImageStrokeResult(BaseModel):
    """Recognition results for a single image-extracted stroke."""
    stroke_id: str
    symbol: str
    family: str
    confidence: float
    circle_is_circle: bool
    hook_is_hook: bool
    length_is_modified: bool
    position: str
    weight: str


class ImageProcessResult(BaseModel):
    """Full recognition pipeline results for an uploaded image."""
    stroke_results: list[ImageStrokeResult]
    phonemes: list[str]
    candidates: list[dict]   # [{"word": str, "confidence": float}]
    phrase_text: str | None
    phrase_confidence: float
    transcript: list[str]    # top-1 candidate per word (empty until user selects)


# ---------------------------------------------------------------------------
# M17 — AI-assisted candidate refinement schemas
# ---------------------------------------------------------------------------

class AIRefinementResult(BaseModel):
    """
    Result of one AI refinement pass.  Follows the M14 standard fields.

    was_invoked:         True when the AI call was attempted (even if it fell back).
    promoted_candidate:  Word moved to rank 1 by AI; None when original rank unchanged
                         or when fallback_used=True.
    confidence_boost:    Confidence delta added to the promoted candidate (0.10 fixed).
    reasoning:           Primary LLM reasoning for the top-ranked word; "" on fallback.
    original_ranking:    Candidate words in their original deterministic order.
    refined_ranking:     Candidate words in AI-refined order; == original on fallback.
    fallback_used:       True when AI failed, timed out, or was skipped by rules.
    detected:            M14 standard; True only when was_invoked=True and not fallback.
    confidence:          M14 standard; confidence of the top refined candidate.
    alternatives:        M14 standard placeholder.
    """
    stroke_id: str
    was_invoked: bool
    promoted_candidate: str | None
    confidence_boost: float
    reasoning: str = ""
    original_ranking: list[str]
    refined_ranking: list[str]
    fallback_used: bool
    detected: bool = False
    confidence: float = 0.0
    alternatives: list = []


# ---------------------------------------------------------------------------
# M13D — Writing position detection schemas
# ---------------------------------------------------------------------------

class PositionResult(BaseModel):
    stroke_id: str
    position: str           # "FIRST" | "SECOND" | "THIRD" | "UNKNOWN"
    confidence: float       # [0, 1]; 0.0 when position = "UNKNOWN"
    alternatives: list = [] # M14 — placeholder; future: ranked alternative positions
    centroid_y: float       # mean Y of all stroke points (canvas px)
    normalized_y: float     # centroid_y / canvas_height → [0, 1]
    canvas_height: float    # canvas height supplied by the client (px)
    reasoning: str = ""     # human-readable explanation; always populated by detector
