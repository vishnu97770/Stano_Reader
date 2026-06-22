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
from recognizer.family_rules import compute_family_score
from recognizer.schemas import FamilyMatch, FamilyResult, StrokeFeatures


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
    )


def classify_from_points(stroke_id: str, points: list[dict]) -> FamilyResult:
    """
    Convenience wrapper: extract features then classify.
    Used by the API endpoint.
    """
    features = analyze_stroke(stroke_id, points)
    return classify_stroke(features)
