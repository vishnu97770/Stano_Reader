"""
Circle and loop detector for Pitman shorthand.

Public interface
────────────────
    detect_circle(stroke_id, features, points) -> CircleResult

The function returns is_circle=False immediately when the stroke does not
pass the gate conditions defined in circle_rules.py.  When it does pass,
it classifies into one of four types and computes a confidence score.

Feature reuse
─────────────
detect_circle() takes pre-computed StrokeFeatures so callers that already
ran analyze_stroke() (e.g. the symbol classifier pipeline) do not pay for
re-extraction.  The raw points list is required only to compute the closure
ratio (dist(first, last) / path_length), which is not in StrokeFeatures.

Future position awareness
─────────────────────────
Today position="ANY".  A future milestone can pass the current outline to
a wrapper function that calls detect_circle() and then sets position based
on the outline length:
  0 strokes so far → "INITIAL"
  N strokes so far → "MEDIAL" or "FINAL" based on next stroke presence.
No change to this file or the API is needed for that extension.
"""

from __future__ import annotations

import math

from recognizer.circle_definitions import CIRCLE_DEFINITIONS
from recognizer.circle_rules import (
    CIRCLE_MAX_CLOSURE,
    CIRCLE_MIN_AREA,
    CIRCLE_MIN_CURVATURE,
    CURVATURE_SATURATION,
    LOOP_ASPECT_THRESHOLD,
    SMALL_SIZE_THRESHOLD_AREA,
    W_CLOSURE,
    W_CURVATURE,
    W_TYPE,
)
from recognizer.schemas import CircleResult, StrokeFeatures


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _closure_ratio(features: StrokeFeatures, points: list[dict]) -> float:
    """
    dist(first_point, last_point) / total_path_length.
    0.0 → perfectly closed loop.
    1.0 → open stroke (start == end only if path_length ≈ 0).
    """
    if features.length < 1e-9:
        return 1.0
    first, last = points[0], points[-1]
    dist = math.sqrt((last["x"] - first["x"]) ** 2 + (last["y"] - first["y"]) ** 2)
    return dist / features.length


def _elongation(features: StrokeFeatures) -> float:
    """max(width, height) / min(width, height) of the bounding box."""
    w = features.bounding_box.width
    h = features.bounding_box.height
    if min(w, h) < 1e-9:
        return float("inf")
    return max(w, h) / min(w, h)


def _bbox_area(features: StrokeFeatures) -> float:
    return features.bounding_box.width * features.bounding_box.height


def _not_circle(stroke_id: str) -> CircleResult:
    return CircleResult(
        stroke_id=stroke_id,
        is_circle=False,
        circle_type=None,
        phoneme=None,
        confidence=0.0,
        position="ANY",
        reasoning=None,
    )


# ---------------------------------------------------------------------------
# Gate check
# ---------------------------------------------------------------------------

def _passes_gate(features: StrokeFeatures, closure: float) -> bool:
    if not features.is_curve:
        return False
    # Treat inf curvature_ratio (perfect closure) as passing
    ratio = features.curvature_ratio
    effective_ratio = CURVATURE_SATURATION if math.isinf(ratio) else ratio
    if effective_ratio < CIRCLE_MIN_CURVATURE:
        return False
    if closure > CIRCLE_MAX_CLOSURE:
        return False
    if _bbox_area(features) < CIRCLE_MIN_AREA:
        return False
    return True


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

def _curvature_conf(features: StrokeFeatures) -> float:
    ratio = features.curvature_ratio
    if math.isinf(ratio):
        return 1.0
    span = CURVATURE_SATURATION - CIRCLE_MIN_CURVATURE
    return min(1.0, (ratio - CIRCLE_MIN_CURVATURE) / span)


def _closure_conf(closure: float) -> float:
    return max(0.0, 1.0 - closure / CIRCLE_MAX_CLOSURE)


def _type_conf(elongation: float, is_loop: bool) -> float:
    """Confidence that the elongation is clearly in the chosen category."""
    if is_loop:
        # Above threshold: how far above the loop boundary?
        excess = elongation - LOOP_ASPECT_THRESHOLD
        return min(1.0, excess / 2.0)
    else:
        # Below threshold: how far below the loop boundary?
        headroom = LOOP_ASPECT_THRESHOLD - elongation
        return min(1.0, max(0.0, headroom / (LOOP_ASPECT_THRESHOLD - 1.0)))


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def detect_circle(
    stroke_id: str,
    features: StrokeFeatures,
    points: list[dict],
) -> CircleResult:
    """
    Classify a stroke as a circle or loop, or return is_circle=False.

    Args:
        stroke_id: UUID echoed into the result.
        features:  Pre-computed StrokeFeatures (from analyze_stroke).
        points:    Raw point list — used only for closure ratio computation.

    Returns:
        CircleResult.  is_circle=False when gate conditions are not met.
    """
    closure = _closure_ratio(features, points)

    if not _passes_gate(features, closure):
        return _not_circle(stroke_id)

    elongation = _elongation(features)
    is_loop = math.isinf(elongation) or elongation >= LOOP_ASPECT_THRESHOLD
    is_large = _bbox_area(features) >= SMALL_SIZE_THRESHOLD_AREA

    if is_loop and is_large:
        circle_type = "LARGE_LOOP"
    elif is_loop:
        circle_type = "SMALL_LOOP"
    elif is_large:
        circle_type = "LARGE_CIRCLE"
    else:
        circle_type = "SMALL_CIRCLE"

    defn = CIRCLE_DEFINITIONS[circle_type]

    curvature_c = _curvature_conf(features)
    closure_c = _closure_conf(closure)
    type_c = _type_conf(
        float("inf") if math.isinf(elongation) else elongation,
        is_loop,
    )

    confidence = round(
        W_CURVATURE * curvature_c + W_CLOSURE * closure_c + W_TYPE * type_c,
        4,
    )

    ratio_str = "∞" if math.isinf(features.curvature_ratio) else f"{features.curvature_ratio:.2f}"
    elong_str = "∞" if math.isinf(elongation) else f"{elongation:.2f}"

    reasoning = (
        f"{circle_type}: curvature={ratio_str}×, "
        f"closure={closure:.2f}, elongation={elong_str}×"
    )

    return CircleResult(
        stroke_id=stroke_id,
        is_circle=True,
        circle_type=circle_type,
        phoneme=defn.phoneme,
        confidence=confidence,
        position=defn.position,
        reasoning=reasoning,
    )
