"""
Pitman halving and doubling detector.

Public interface
----------------
    detect_length(stroke_id, features, family_name=None) -> LengthResult

The detector compares features.length against the canonical length for the
given family (or the global fallback when family is unknown) and returns
whether the stroke is HALF or DOUBLE length, plus the added phoneme and
confidence.
"""

from recognizer.length_definitions import (
    GLOBAL_CANONICAL_PX,
    GLOBAL_DOUBLE_PHONEME,
    GLOBAL_HALF_PHONEME,
    LENGTH_DEFINITIONS,
)
from recognizer.length_rules import (
    DOUBLE_RATIO_CENTER,
    DOUBLE_RATIO_MAX,
    DOUBLE_RATIO_MIN,
    HALF_RATIO_CENTER,
    HALF_RATIO_MAX,
    HALF_RATIO_MIN,
    LENGTH_MIN_PX,
    MAX_CURVATURE_RATIO,
    W_LENGTH,
    W_RATIO,
    length_confidence,
    ratio_confidence,
)
from recognizer.schemas import LengthResult, StrokeFeatures


def _resolve_canonical(family_name: str | None) -> tuple[float, str, str]:
    """Return (canonical_px, half_phoneme, double_phoneme) for the given family."""
    if family_name and family_name in LENGTH_DEFINITIONS:
        defn = LENGTH_DEFINITIONS[family_name]
        return defn.canonical_px, defn.half_phoneme, defn.double_phoneme
    return GLOBAL_CANONICAL_PX, GLOBAL_HALF_PHONEME, GLOBAL_DOUBLE_PHONEME


def _not_modified(
    stroke_id: str,
    measured: float,
    canonical: float,
    ratio: float,
    reason: str,
) -> LengthResult:
    return LengthResult(
        stroke_id=stroke_id,
        is_modified=False,
        modification_type=None,
        added_phoneme=None,
        confidence=0.0,
        canonical_length=canonical,
        measured_length=measured,
        length_ratio=round(ratio, 3),
        reasoning=None,
    )


def detect_length(
    stroke_id: str,
    features: StrokeFeatures,
    family_name: str | None = None,
) -> LengthResult:
    """
    Detect whether a stroke is drawn at half or double its canonical length.

    Parameters
    ----------
    stroke_id   : stroke identifier (echoed into result)
    features    : pre-computed StrokeFeatures from analyze_stroke()
    family_name : optional Pitman family key (e.g. "PB_FAMILY"); when None,
                  the global canonical length is used as the reference
    """
    measured = features.length
    canonical, half_phoneme, double_phoneme = _resolve_canonical(family_name)
    ratio = measured / canonical if canonical > 0 else 0.0

    # ── Gate: too short to measure reliably ──────────────────────────────────
    if measured < LENGTH_MIN_PX:
        return _not_modified(stroke_id, measured, canonical, ratio, "stroke too short")

    # ── Gate: curved strokes are circles/loops, not consonant strokes ─────────
    if features.curvature_ratio >= MAX_CURVATURE_RATIO:
        return _not_modified(stroke_id, measured, canonical, ratio, "curved stroke excluded")

    # ── Check HALF band ───────────────────────────────────────────────────────
    if HALF_RATIO_MIN <= ratio <= HALF_RATIO_MAX:
        r_conf = ratio_confidence(ratio, HALF_RATIO_CENTER, HALF_RATIO_MIN, HALF_RATIO_MAX)
        l_conf = length_confidence(measured)
        confidence = round(W_RATIO * r_conf + W_LENGTH * l_conf, 3)
        reasoning = (
            f"length {measured:.1f}px is {ratio:.2f}× canonical {canonical:.0f}px "
            f"(half band [{HALF_RATIO_MIN}–{HALF_RATIO_MAX}]); "
            f"adds {half_phoneme}"
        )
        return LengthResult(
            stroke_id=stroke_id,
            is_modified=True,
            modification_type="HALF",
            added_phoneme=half_phoneme,
            confidence=confidence,
            canonical_length=canonical,
            measured_length=measured,
            length_ratio=round(ratio, 3),
            reasoning=reasoning,
        )

    # ── Check DOUBLE band ─────────────────────────────────────────────────────
    if DOUBLE_RATIO_MIN <= ratio <= DOUBLE_RATIO_MAX:
        r_conf = ratio_confidence(ratio, DOUBLE_RATIO_CENTER, DOUBLE_RATIO_MIN, DOUBLE_RATIO_MAX)
        l_conf = length_confidence(measured)
        confidence = round(W_RATIO * r_conf + W_LENGTH * l_conf, 3)
        reasoning = (
            f"length {measured:.1f}px is {ratio:.2f}× canonical {canonical:.0f}px "
            f"(double band [{DOUBLE_RATIO_MIN}–{DOUBLE_RATIO_MAX}]); "
            f"adds {double_phoneme}"
        )
        return LengthResult(
            stroke_id=stroke_id,
            is_modified=True,
            modification_type="DOUBLE",
            added_phoneme=double_phoneme,
            confidence=confidence,
            canonical_length=canonical,
            measured_length=measured,
            length_ratio=round(ratio, 3),
            reasoning=reasoning,
        )

    # ── Normal stroke ─────────────────────────────────────────────────────────
    return _not_modified(stroke_id, measured, canonical, ratio, "normal length")
