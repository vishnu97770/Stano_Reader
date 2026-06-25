"""
Stroke weight classification: LIGHT, HEAVY, or AMBIGUOUS.

In Pitman shorthand, 'weight' maps to voiced/unvoiced:
  LIGHT  → unvoiced consonant (P, T, K, CH, F, TH, S, SH)
  HEAVY  → voiced consonant   (B, D, G, J,  V, DH, Z, ZH)
  AMBIGUOUS → middle zone; typical for mouse input (constant 0.5 pressure)

Thresholds are module-level constants — easy to locate and adjust.
To make them runtime-configurable, load from env vars here; no other
code needs to change.
"""

from recognizer.pressure import compute_pressure_stats
from recognizer.schemas import WeightResult

# ---------------------------------------------------------------------------
# Configurable thresholds
# ---------------------------------------------------------------------------
# Symmetric around 0.5 (the mouse-device default from the W3C spec).
# The AMBIGUOUS zone covers the range where mouse input always falls.
LIGHT_THRESHOLD: float = 0.35
HEAVY_THRESHOLD: float = 0.65

_LIGHT = "LIGHT"
_HEAVY = "HEAVY"
_AMBIGUOUS = "AMBIGUOUS"


def _label_from_avg(avg: float) -> str:
    if avg <= LIGHT_THRESHOLD:
        return _LIGHT
    if avg >= HEAVY_THRESHOLD:
        return _HEAVY
    return _AMBIGUOUS


def classify_weight(stroke_id: str, points: list[dict]) -> WeightResult:
    """
    Classify a stroke as LIGHT, HEAVY, or AMBIGUOUS based on its average
    input pressure.

    Args:
        stroke_id: UUID of the stroke (echoed into the result).
        points:    Raw point dicts; each may optionally carry a 'pressure' key.

    Returns:
        WeightResult.  When no point carries pressure data, avg and max are
        reported as 0.5 (the neutral/ambiguous level) and weight = AMBIGUOUS.
    """
    stats = compute_pressure_stats(points)

    if stats is None:
        # No pressure data at all (pre-M7 strokes, test clients without pressure)
        return WeightResult(
            stroke_id=stroke_id,
            weight=_AMBIGUOUS,
            avg_pressure=0.5,
            max_pressure=0.5,
            variance=0.0,
            threshold_light=LIGHT_THRESHOLD,
            threshold_heavy=HEAVY_THRESHOLD,
        )

    return WeightResult(
        stroke_id=stroke_id,
        weight=_label_from_avg(stats["avg_pressure"]),
        avg_pressure=stats["avg_pressure"],
        max_pressure=stats["max_pressure"],
        variance=stats["variance"],
        threshold_light=LIGHT_THRESHOLD,
        threshold_heavy=HEAVY_THRESHOLD,
    )
