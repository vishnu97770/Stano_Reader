"""
Pure scoring functions for Pitman family classification.

All functions take StrokeFeatures and FamilyDefinition and return a float in [0, 1].
No I/O, no side effects — fully testable in isolation.

Score composition per family:
    raw_score = 0.60 * angle_score
              + 0.30 * shape_score
              + 0.10 * aspect_score

SZ_FAMILY uses a different formula (circle scoring replaces angle scoring).
"""

import math

from recognizer.family_definitions import FamilyDefinition
from recognizer.schemas import StrokeFeatures

# ---------------------------------------------------------------------------
# Signal weights
# ---------------------------------------------------------------------------
W_ANGLE = 0.60
W_SHAPE = 0.30
W_ASPECT = 0.10

# Curvature thresholds for S/Z circle detection
_SZ_STRONG_RATIO = 3.0   # path length ≥ 3× chord → likely a closed loop
_SZ_WEAK_RATIO = 1.8     # path length ≥ 1.8× chord → loose oval

# Aspect ratio that counts as "tall" or "wide"
_ASPECT_DOMINANT_RATIO = 1.5


# ---------------------------------------------------------------------------
# Angle scoring
# ---------------------------------------------------------------------------

def _circular_diff(a: float, b: float) -> float:
    """Minimum angular difference between two bearings, in [0, 180]."""
    diff = abs(a - b) % 360.0
    return diff if diff <= 180.0 else 360.0 - diff


def score_angle(features: StrokeFeatures, center: float, tolerance: float) -> float:
    """
    Linear falloff from the expected angle center.
    Returns 1.0 at center, 0.0 when diff >= tolerance, linear between.
    Handles circular wraparound (e.g. center=0° spans 345-15°).
    """
    if tolerance >= 360.0:
        # SZ_FAMILY accepts any angle; signal is irrelevant
        return 1.0
    diff = _circular_diff(features.angle, center)
    if diff >= tolerance:
        return 0.0
    return 1.0 - (diff / tolerance)


# ---------------------------------------------------------------------------
# Shape scoring
# ---------------------------------------------------------------------------

def score_shape(features: StrokeFeatures, expect_curve: bool) -> float:
    """
    Returns 1.0 when shape matches expectation, 0.1 when it does not.
    The 0.1 floor (instead of 0.0) lets borderline strokes accumulate
    partial credit rather than being completely eliminated by noise.
    """
    matches = features.is_curve == expect_curve
    return 1.0 if matches else 0.1


def score_circle(features: StrokeFeatures) -> float:
    """
    Specialised shape score for SZ_FAMILY.
    High curvature ratio + is_curve = circle-like stroke.
    """
    if not features.is_curve:
        return 0.0

    ratio = features.curvature_ratio

    if math.isinf(ratio) or ratio >= _SZ_STRONG_RATIO:
        return 1.0
    if ratio >= _SZ_WEAK_RATIO:
        # Linear interpolation between weak and strong thresholds
        t = (ratio - _SZ_WEAK_RATIO) / (_SZ_STRONG_RATIO - _SZ_WEAK_RATIO)
        return 0.4 + 0.6 * t
    # Below weak threshold: still curved but not circle-like
    return max(0.0, (ratio - 1.0) / (_SZ_WEAK_RATIO - 1.0) * 0.4)


# ---------------------------------------------------------------------------
# Aspect ratio scoring
# ---------------------------------------------------------------------------

def _aspect_ratio(features: StrokeFeatures) -> float:
    """width / height of the bounding box. Returns 0 if degenerate."""
    h = features.bounding_box.height
    w = features.bounding_box.width
    if h < 1e-3 and w < 1e-3:
        return 1.0  # degenerate stroke — treat as balanced
    if h < 1e-3:
        return float("inf")
    return w / h


def score_aspect(features: StrokeFeatures, hint: str) -> float:
    """
    Scores bounding-box aspect ratio against the family's expected shape.

    hint = "tall"     → expects height significantly > width  (w/h < 1)
    hint = "wide"     → expects width significantly > height  (w/h > 1)
    hint = "balanced" → expects width ≈ height                (w/h ≈ 1)
    hint = "square"   → same as balanced (used by SZ_FAMILY)
    """
    ratio = _aspect_ratio(features)

    if hint in ("balanced", "square"):
        # Score peaks when ratio ≈ 1, falls off symmetrically
        deviation = abs(ratio - 1.0)
        return max(0.0, 1.0 - deviation / _ASPECT_DOMINANT_RATIO)

    if hint == "wide":
        # Score peaks when ratio >= _ASPECT_DOMINANT_RATIO
        if ratio >= _ASPECT_DOMINANT_RATIO:
            return 1.0
        return ratio / _ASPECT_DOMINANT_RATIO

    if hint == "tall":
        # w/h should be < 1 (i.e. height > width); equivalent to h/w > 1
        inv_ratio = 1.0 / ratio if ratio > 1e-9 else float("inf")
        if inv_ratio >= _ASPECT_DOMINANT_RATIO:
            return 1.0
        return inv_ratio / _ASPECT_DOMINANT_RATIO

    return 0.5  # unknown hint — neutral


# ---------------------------------------------------------------------------
# Combined family score
# ---------------------------------------------------------------------------

def compute_family_score(features: StrokeFeatures, defn: FamilyDefinition) -> float:
    """
    Returns the overall match score ∈ [0, 1] for one family.

    SZ_FAMILY uses circle scoring in place of angle+shape (it has no
    meaningful directional angle).  All other families use the standard
    weighted combination.

    Shape mismatch is a hard gate: when the stroke's curvature type does not
    match the family's expectation, the score is capped at 0.15 regardless of
    angle or aspect.  This prevents spurious high-confidence alternatives
    (e.g. THDH scoring 0.70 for a circle stroke because the degenerate chord
    angle happens to be 0°).
    """
    if defn.name == "SZ_FAMILY":
        circle = score_circle(features)
        aspect = score_aspect(features, defn.aspect_hint)
        # Circle likeness carries most of the weight for S/Z
        return round(0.80 * circle + 0.20 * aspect, 4)

    # Hard gate: wrong shape type cannot produce a meaningful match.
    # Scored at 0.05 so wrong-shape strokes are far below CONFIDENCE_THRESHOLD
    # and just barely above zero (they can still form a very distant alternative).
    if features.is_curve != defn.expect_curve:
        return 0.05

    # Shape is confirmed correct; fold its weight into angle (the primary signal).
    angle = score_angle(features, defn.angle_center, defn.angle_tolerance)
    aspect = score_aspect(features, defn.aspect_hint)

    # W_ANGLE + W_SHAPE = 0.90 → angle is dominant; aspect is tie-breaker.
    return round((W_ANGLE + W_SHAPE) * angle + W_ASPECT * aspect, 4)
