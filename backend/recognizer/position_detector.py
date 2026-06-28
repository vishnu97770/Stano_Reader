"""
Pitman writing position detector.

Public interface
----------------
    detect_position(
        stroke_id, points, canvas_height,
        baseline_mode="VIRTUAL"
    ) -> PositionResult

Determines whether a stroke is written in FIRST, SECOND, or THIRD
Pitman position based on where the stroke's centroid Y falls relative
to two virtual guide lines that divide the canvas into equal thirds.

No StrokeFeatures are needed — only raw points and canvas_height.
This keeps the endpoint lightweight and avoids redundant computation.

Future baseline modes (PITMAN_RULED, SCANNED, CUSTOM) are selected by
the baseline_mode parameter and would inject alternative LINE1/LINE2
fractions without changing this file's public signature.
"""

from recognizer.position_definitions import (
    BASELINE_MODE_VIRTUAL,
    POSITION_DEFINITIONS,
)
from recognizer.position_rules import (
    MIN_CANVAS_HEIGHT_PX,
    classify_band,
    compute_centroid_y,
    position_confidence,
)
from recognizer.schemas import PositionResult


def _unknown(stroke_id: str, canvas_height: float, reason: str) -> PositionResult:
    return PositionResult(
        stroke_id=stroke_id,
        position="UNKNOWN",
        confidence=0.0,
        centroid_y=0.0,
        normalized_y=0.0,
        canvas_height=canvas_height,
        reasoning=reason,
    )


def detect_position(
    stroke_id: str,
    points: list[dict],
    canvas_height: float,
    baseline_mode: str = BASELINE_MODE_VIRTUAL,
) -> PositionResult:
    """
    Classify the writing position of a stroke.

    Parameters
    ----------
    stroke_id     : stroke identifier (echoed into result)
    points        : raw stroke points, each dict with at least {x, y}
    canvas_height : visible canvas height in CSS pixels; sent by the client
    baseline_mode : reference line system; only "VIRTUAL" is implemented
    """
    # ── Gate: usable canvas height ────────────────────────────────────────────
    if canvas_height <= MIN_CANVAS_HEIGHT_PX:
        return _unknown(stroke_id, canvas_height, "canvas_height is too small to determine position")

    # ── Gate: at least one point ──────────────────────────────────────────────
    if not points:
        return _unknown(stroke_id, canvas_height, "no points provided")

    # ── Compute centroid ──────────────────────────────────────────────────────
    centroid_y = compute_centroid_y(points)

    # Clamp: points outside canvas bounds still produce a valid result
    norm_y = max(0.0, min(1.0, centroid_y / canvas_height))

    # ── Classify ──────────────────────────────────────────────────────────────
    band = classify_band(norm_y)
    confidence = position_confidence(norm_y, band)
    defn = POSITION_DEFINITIONS[band]

    reasoning = (
        f"Centroid Y {centroid_y:.1f}px (normalized {norm_y:.3f}) "
        f"lies in {defn.label.lower()} zone ({band}). "
        f"{defn.description}."
    )

    return PositionResult(
        stroke_id=stroke_id,
        position=band,
        confidence=confidence,
        centroid_y=round(centroid_y, 2),
        normalized_y=round(norm_y, 4),
        canvas_height=canvas_height,
        reasoning=reasoning,
    )
