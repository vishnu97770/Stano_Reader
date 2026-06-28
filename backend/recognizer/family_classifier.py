"""
Orchestrates Pitman family classification.

Pipeline:
    raw points
        → analyze_stroke()       [features.py / analyzer.py]
        → classify_stroke()      [this file]
        → FamilyResult

classify_stroke() takes pre-computed StrokeFeatures so callers that already
have features from M4's analyze_stroke() do not pay for re-computation.
The /api/classify-family endpoint computes features internally and calls
classify_stroke().
"""

from recognizer.analyzer import analyze_stroke
from recognizer.family_definitions import (
    ALL_FAMILIES,
    ALTERNATIVE_THRESHOLD,
    CONFIDENCE_THRESHOLD,
    FAMILY_DEFINITIONS,
)
from recognizer.family_rules import (
    compute_family_score,
    score_angle,
    score_aspect,
    score_circle,
)
from recognizer.schemas import FamilyMatch, FamilyResult, StrokeFeatures


def _angle_diff(a: float, b: float) -> float:
    """Minimum angular difference between two bearings, in [0, 180]."""
    diff = abs(a - b) % 360.0
    return diff if diff <= 180.0 else 360.0 - diff


def _build_reasoning(features: StrokeFeatures, family: str, score: float) -> str:
    """
    Plain-English explanation of why the stroke matched (or didn't match) a family.
    Only called for the winning family; the UNKNOWN path uses its own message.
    """
    defn = FAMILY_DEFINITIONS[family]

    if family == "SZ_FAMILY":
        circle_s = score_circle(features)
        aspect_s = score_aspect(features, defn.aspect_hint)
        return (
            f"{family}: curvature_ratio={features.curvature_ratio:.2f} "
            f"(circle_score={circle_s:.2f}), "
            f"is_curve={features.is_curve}, "
            f"aspect_score={aspect_s:.2f}; "
            f"final_score={score:.4f}"
        )

    # Straight-stroke families
    diff = _angle_diff(features.angle, defn.angle_center)
    angle_s = score_angle(features, defn.angle_center, defn.angle_tolerance)
    aspect_s = score_aspect(features, defn.aspect_hint)
    shape_ok = "matches" if features.is_curve == defn.expect_curve else "mismatch"
    return (
        f"{family}: angle={features.angle:.1f}° vs expected {defn.angle_center:.0f}° "
        f"(diff={diff:.1f}°, tol={defn.angle_tolerance:.0f}°, angle_score={angle_s:.2f}), "
        f"is_curve={features.is_curve} ({shape_ok}), "
        f"aspect_score={aspect_s:.2f}; "
        f"final_score={score:.4f}"
    )


def classify_stroke(features: StrokeFeatures) -> FamilyResult:
    """
    Classify a stroke into a Pitman symbol family.

    Args:
        features: Pre-computed StrokeFeatures from analyze_stroke().

    Returns:
        FamilyResult with the best family, its confidence, and alternatives
        above the noise floor.  family = "UNKNOWN" when no family clears
        CONFIDENCE_THRESHOLD.
    """
    # Score every family
    scores: dict[str, float] = {
        name: compute_family_score(features, FAMILY_DEFINITIONS[name])
        for name in ALL_FAMILIES
    }

    # Sort descending by score
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    best_family, best_score = ranked[0]

    if best_score < CONFIDENCE_THRESHOLD:
        return FamilyResult(
            stroke_id=features.stroke_id,
            family="UNKNOWN",
            confidence=0.0,
            alternatives=[],
            reasoning=(
                f"UNKNOWN: best candidate {best_family} scored {best_score:.4f}, "
                f"below confidence threshold {CONFIDENCE_THRESHOLD}"
            ),
        )

    alternatives = [
        FamilyMatch(family=name, confidence=score)
        for name, score in ranked[1:]
        if score >= ALTERNATIVE_THRESHOLD
    ]

    return FamilyResult(
        stroke_id=features.stroke_id,
        family=best_family,
        confidence=best_score,
        alternatives=alternatives,
        reasoning=_build_reasoning(features, best_family, best_score),
    )


def classify_from_points(stroke_id: str, points: list[dict]) -> FamilyResult:
    """
    Convenience wrapper: extract features then classify.
    Used by the API endpoint.
    """
    features = analyze_stroke(stroke_id, points)
    return classify_stroke(features)
