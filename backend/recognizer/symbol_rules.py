"""
Pure symbol scoring functions.

All functions are side-effect-free and take only StrokeFeatures + family name.
No I/O, no Pydantic, no FastAPI — fully testable in isolation.

M6: When pressure_stats is None, scoring falls back to English phoneme
    frequency priors and returns thickness_missing=True.

M7: When pressure_stats is present, _score_from_pressure() is called.
    Voiced/unvoiced distinction is determined by average pressure against
    configurable thresholds.  thickness_missing becomes False.
"""

from recognizer.schemas import StrokeFeatures
from recognizer.symbol_definitions import (
    FAMILY_SYMBOLS,
    SYMBOL_DEFINITIONS,
    THICKNESS_MISSING_CONFIDENCE_CAP,
    THICKNESS_MISSING_REASON,
)
from recognizer.weight_classifier import HEAVY_THRESHOLD, LIGHT_THRESHOLD

# ---------------------------------------------------------------------------
# English phoneme frequency priors (fallback when pressure is unavailable)
# ---------------------------------------------------------------------------
_FREQUENCY_PRIORS: dict[str, dict[str, float]] = {
    "PB_FAMILY":   {"P":  0.52, "B":  0.48},
    "TD_FAMILY":   {"T":  0.54, "D":  0.46},
    "KG_FAMILY":   {"K":  0.53, "G":  0.47},
    "CHJ_FAMILY":  {"CH": 0.52, "J":  0.48},
    "FV_FAMILY":   {"F":  0.53, "V":  0.47},
    "THDH_FAMILY": {"DH": 0.56, "TH": 0.44},
    "SZ_FAMILY":   {"S":  0.62, "Z":  0.38},
    "SHZH_FAMILY": {"SH": 0.54, "ZH": 0.46},
}

# Maximum confidence achievable via pressure scoring.
# 0.92 allows for slight hardware noise even at extremes.
_PRESSURE_CONFIDENCE_CAP = 0.92


# ---------------------------------------------------------------------------
# Public scoring entry point
# ---------------------------------------------------------------------------

def compute_symbol_scores(
    features: StrokeFeatures,
    family: str,
) -> tuple[dict[str, float], bool, str | None]:
    """
    Return (scores, thickness_missing, reason).

    scores:            symbol → confidence value ∈ [0, 1]
    thickness_missing: True when pressure data was unavailable for this decision
    reason:            human-readable explanation (None when thickness IS available)
    """
    if family not in FAMILY_SYMBOLS or family not in _FREQUENCY_PRIORS:
        return {}, True, f"No symbol data for family '{family}'"

    if features.pressure_stats is not None:
        return _score_from_pressure(features, family), False, None

    priors = _FREQUENCY_PRIORS[family]
    scores = {sym: min(conf, THICKNESS_MISSING_CONFIDENCE_CAP) for sym, conf in priors.items()}
    return scores, True, THICKNESS_MISSING_REASON


# ---------------------------------------------------------------------------
# Pressure-based scoring (M7)
# ---------------------------------------------------------------------------

def _score_from_pressure(
    features: StrokeFeatures,
    family: str,
) -> dict[str, float]:
    """
    Score voiced vs unvoiced using average pressure against thresholds.

    Zones:
      avg ≤ LIGHT_THRESHOLD (0.35):   unvoiced 0.92, voiced 0.08
      avg ≥ HEAVY_THRESHOLD (0.65):   voiced   0.92, unvoiced 0.08
      middle:                          linear interpolation between the two

    Uses SYMBOL_DEFINITIONS[sym].is_voiced so the correct symbol gets each
    score regardless of tuple ordering in FAMILY_SYMBOLS (THDH_FAMILY has
    DH listed first for frequency reasons, but DH is the voiced symbol).
    """
    avg = features.pressure_stats.avg_pressure  # type: ignore[union-attr]
    symbols = FAMILY_SYMBOLS[family]

    unvoiced_sym = next(s for s in symbols if not SYMBOL_DEFINITIONS[s].is_voiced)
    voiced_sym   = next(s for s in symbols if     SYMBOL_DEFINITIONS[s].is_voiced)

    if avg <= LIGHT_THRESHOLD:
        voiced_conf   = 1.0 - _PRESSURE_CONFIDENCE_CAP   # 0.08
        unvoiced_conf = _PRESSURE_CONFIDENCE_CAP          # 0.92
    elif avg >= HEAVY_THRESHOLD:
        voiced_conf   = _PRESSURE_CONFIDENCE_CAP          # 0.92
        unvoiced_conf = 1.0 - _PRESSURE_CONFIDENCE_CAP   # 0.08
    else:
        # Linear interpolation across the ambiguous middle zone
        t = (avg - LIGHT_THRESHOLD) / (HEAVY_THRESHOLD - LIGHT_THRESHOLD)
        # t=0 → (unvoiced=0.92, voiced=0.08); t=1 → (voiced=0.92, unvoiced=0.08)
        swing = _PRESSURE_CONFIDENCE_CAP - (1.0 - _PRESSURE_CONFIDENCE_CAP)  # 0.84
        voiced_conf   = (1.0 - _PRESSURE_CONFIDENCE_CAP) + swing * t
        unvoiced_conf = _PRESSURE_CONFIDENCE_CAP - swing * t

    return {
        unvoiced_sym: round(unvoiced_conf, 4),
        voiced_sym:   round(voiced_conf,   4),
    }
