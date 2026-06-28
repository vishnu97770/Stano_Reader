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


def _weight_confidence(avg: float, weight: str) -> float:
    """
    Confidence in [0, 1] based on how far the measured pressure is from the
    classification boundary.

    LIGHT   → distance below LIGHT_THRESHOLD  (1.0 at pressure=0,  0.0 at threshold)
    HEAVY   → distance above HEAVY_THRESHOLD  (1.0 at pressure=1,  0.0 at threshold)
    AMBIGUOUS → distance from nearest threshold (1.0 at midpoint,   0.0 at either edge)
    """
    if weight == _LIGHT:
        if LIGHT_THRESHOLD < 1e-9:
            return 1.0
        return round(min(1.0, (LIGHT_THRESHOLD - avg) / LIGHT_THRESHOLD), 3)
    if weight == _HEAVY:
        remaining = 1.0 - HEAVY_THRESHOLD
        if remaining < 1e-9:
            return 1.0
        return round(min(1.0, (avg - HEAVY_THRESHOLD) / remaining), 3)
    # AMBIGUOUS: distance from the nearest threshold, scaled to the half-band
    margin = min(avg - LIGHT_THRESHOLD, HEAVY_THRESHOLD - avg)
    band_half = (HEAVY_THRESHOLD - LIGHT_THRESHOLD) / 2.0
    if band_half < 1e-9:
        return 0.0
    return round(min(1.0, max(0.0, margin / band_half)), 3)


def _weight_reasoning(avg: float, weight: str, has_pressure: bool) -> str:
    """Plain-English explanation of the weight classification."""
    if not has_pressure:
        return "no pressure data available; classification defaults to AMBIGUOUS"
    if weight == _LIGHT:
        margin = round(LIGHT_THRESHOLD - avg, 4)
        return (
            f"avg_pressure {avg:.4f} is below light threshold {LIGHT_THRESHOLD} "
            f"(margin {margin:.4f})"
        )
    if weight == _HEAVY:
        margin = round(avg - HEAVY_THRESHOLD, 4)
        return (
            f"avg_pressure {avg:.4f} exceeds heavy threshold {HEAVY_THRESHOLD} "
            f"(margin {margin:.4f})"
        )
    # AMBIGUOUS
    dist_light = round(avg - LIGHT_THRESHOLD, 4)
    dist_heavy = round(HEAVY_THRESHOLD - avg, 4)
    return (
        f"avg_pressure {avg:.4f} lies in ambiguous zone "
        f"[{LIGHT_THRESHOLD}–{HEAVY_THRESHOLD}]; "
        f"{dist_light:.4f} above light threshold, {dist_heavy:.4f} below heavy threshold"
    )


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
            confidence=0.0,
            reasoning=_weight_reasoning(0.5, _AMBIGUOUS, has_pressure=False),
        )

    avg = stats["avg_pressure"]
    weight = _label_from_avg(avg)
    return WeightResult(
        stroke_id=stroke_id,
        weight=weight,
        avg_pressure=avg,
        max_pressure=stats["max_pressure"],
        variance=stats["variance"],
        threshold_light=LIGHT_THRESHOLD,
        threshold_heavy=HEAVY_THRESHOLD,
        confidence=_weight_confidence(avg, weight),
        reasoning=_weight_reasoning(avg, weight, has_pressure=True),
    )
