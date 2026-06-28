"""
Vowel sign detector — public API.

Public function: detect_vowel(stroke_id, points, nearby_strokes)

Pipeline:
    raw points + nearby consonant descriptors
        → classify_mark (dot / dash / None via vowel_rules)
        → find_nearest_consonant
        → detect_degree + detect_position
        → look up VowelDefinition in VOWEL_BY_KEY
        → return VowelResult

When the stroke is too large to be a vowel mark, VowelResult.is_vowel = False.
"""

from recognizer.schemas import VowelResult
from recognizer.vowel_rules import (
    NearbyConsonant,
    Point,
    resolve_vowel,
)


def detect_vowel(
    stroke_id: str,
    points: list[dict],
    nearby_strokes: list[dict] | None = None,
) -> VowelResult:
    """
    Detect whether a stroke is a Pitman vowel sign.

    Args:
        stroke_id:      UUID of the stroke being analysed.
        points:         Raw stroke points; each is a dict with at least
                        'x' and 'y' keys (float).  Pressure is ignored.
        nearby_strokes: List of consonant stroke descriptors in scope.
                        Each dict must contain:
                          stroke_id    str
                          family       str
                          centroid_x   float
                          centroid_y   float
                          start_x      float
                          start_y      float
                          end_x        float
                          end_y        float
                        May be None or empty; the detector still classifies the
                        mark type but cannot attach it to a consonant.

    Returns:
        VowelResult.  When is_vowel=False, all optional fields are None and
        confidence is 0.0.
    """
    _nearby: list[dict] = nearby_strokes or []

    # Convert raw dicts to typed objects
    pts = [Point(x=float(p["x"]), y=float(p["y"])) for p in points]
    consonants = [
        NearbyConsonant(
            stroke_id=str(s["stroke_id"]),
            family=str(s["family"]),
            centroid=Point(float(s["centroid_x"]), float(s["centroid_y"])),
            start=Point(float(s["start_x"]), float(s["start_y"])),
            end=Point(float(s["end_x"]), float(s["end_y"])),
        )
        for s in _nearby
    ]

    defn, nearest, confidence, reasoning = resolve_vowel(pts, consonants)

    if defn is None:
        return VowelResult(
            stroke_id=stroke_id,
            is_vowel=False,
            vowel_symbol=None,
            ipa=None,
            degree=None,
            position=None,
            attached_to_stroke_id=None,
            confidence=0.0,
            reasoning=reasoning,
            alternatives=[],
            detected=False,
        )

    return VowelResult(
        stroke_id=stroke_id,
        is_vowel=True,
        vowel_symbol=defn.symbol,
        ipa=defn.ipa,
        degree=defn.degree,
        position=defn.position,
        attached_to_stroke_id=nearest.stroke_id if nearest else None,
        confidence=confidence,
        reasoning=reasoning,
        alternatives=[],
        detected=True,
    )
