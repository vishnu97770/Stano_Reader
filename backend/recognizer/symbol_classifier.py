"""
Orchestrates exact Pitman symbol classification.

Pipeline:
    raw points
        → analyze_stroke()        [M4 — features.py / analyzer.py]
        → classify_stroke()       [M5 — family_classifier.py]
        → classify_symbol()       [M6 — this file]
        → SymbolResult

classify_symbol() takes pre-computed StrokeFeatures and FamilyResult so that
callers who already ran M4/M5 do not pay for re-computation.  The API endpoint
classify_symbol_from_points() is a convenience wrapper that runs all three
steps internally.
"""

from recognizer.analyzer import analyze_stroke
from recognizer.family_classifier import classify_stroke
from recognizer.schemas import FamilyResult, StrokeFeatures, SymbolMatch, SymbolResult
from recognizer.symbol_rules import compute_symbol_scores

# Minimum score for a symbol to appear in the alternatives list
_ALTERNATIVE_THRESHOLD = 0.10


def classify_symbol(
    features: StrokeFeatures,
    family_result: FamilyResult,
) -> SymbolResult:
    """
    Classify a stroke into an exact Pitman symbol.

    Args:
        features:      Pre-computed StrokeFeatures (from analyze_stroke).
        family_result: Pre-computed FamilyResult (from classify_stroke).

    Returns:
        SymbolResult with the best symbol, its confidence, alternatives, and
        metadata about whether pressure data was required but unavailable.
    """
    if family_result.family == "UNKNOWN":
        return SymbolResult(
            stroke_id=features.stroke_id,
            family="UNKNOWN",
            family_confidence=0.0,
            symbol="UNKNOWN",
            confidence=0.0,
            alternatives=[],
            thickness_missing=True,
            reason="Family classification failed — cannot determine symbol",
        )

    scores, thickness_missing, reason = compute_symbol_scores(
        features, family_result.family
    )

    if not scores:
        return SymbolResult(
            stroke_id=features.stroke_id,
            family=family_result.family,
            family_confidence=family_result.confidence,
            symbol="UNKNOWN",
            confidence=0.0,
            alternatives=[],
            thickness_missing=thickness_missing,
            reason=reason,
        )

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    best_symbol, best_conf = ranked[0]

    alternatives = [
        SymbolMatch(symbol=sym, confidence=conf)
        for sym, conf in ranked[1:]
        if conf >= _ALTERNATIVE_THRESHOLD
    ]

    return SymbolResult(
        stroke_id=features.stroke_id,
        family=family_result.family,
        family_confidence=family_result.confidence,
        symbol=best_symbol,
        confidence=best_conf,
        alternatives=alternatives,
        thickness_missing=thickness_missing,
        reason=reason,
    )


def classify_symbol_from_points(stroke_id: str, points: list[dict]) -> SymbolResult:
    """
    Convenience wrapper: run the full M4 → M5 → M6 pipeline from raw points.
    Used by the /api/classify-symbol endpoint.
    """
    features = analyze_stroke(stroke_id, points)
    family_result = classify_stroke(features)
    return classify_symbol(features, family_result)


# M14 I-9 — standardized detect_ prefix alias
detect_symbol = classify_symbol
