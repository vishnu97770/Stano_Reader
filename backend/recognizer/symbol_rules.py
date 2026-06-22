"""
Pure symbol scoring functions.

All functions are side-effect-free and take only StrokeFeatures + family name.
No I/O, no Pydantic, no FastAPI — fully testable in isolation.

Current state (M6):
    All 8 Pitman families are thickness-dependent.  Geometric features (angle,
    curvature, length, aspect) cannot distinguish the two members of any pair.
    Scoring therefore uses English phoneme frequency priors and returns
    thickness_missing=True with a capped confidence ceiling.

Future state (when pressure data is available):
    Add a StrokePressure dataclass to StrokeFeatures, then implement
    score_from_pressure() here.  The caller (compute_symbol_scores) checks
    whether features.pressure is not None before calling it.  No other
    changes needed — SymbolResult already carries thickness_missing: bool
    and reason: str as the signal to consumers.
"""

from recognizer.schemas import StrokeFeatures
from recognizer.symbol_definitions import (
    FAMILY_SYMBOLS,
    THICKNESS_MISSING_CONFIDENCE_CAP,
    THICKNESS_MISSING_REASON,
)

# ---------------------------------------------------------------------------
# English phoneme frequency priors
# ---------------------------------------------------------------------------
# These values reflect relative frequency of each phoneme as an initial
# consonant in English text (approximate, derived from corpus linguistics).
# They are used ONLY when thickness data is absent.
# Confidence values are deliberately kept below 0.65 to reflect honest
# uncertainty.  They do NOT sum to 1.0 — these are match scores, not
# a probability distribution.
#
# Source of bias direction:
#   - Unvoiced consonants (T, K, P, F, CH, SH) are slightly more frequent
#     as word-initial consonants in English.
#   - Exception: DH (/ð/ "the", "this", "that") is the most frequent
#     consonant phoneme in spoken English and outranks TH (/θ/).
#   - S significantly outranks Z.

_FREQUENCY_PRIORS: dict[str, dict[str, float]] = {
    "PB_FAMILY":   {"P":  0.52, "B":  0.48},
    "TD_FAMILY":   {"T":  0.54, "D":  0.46},
    "KG_FAMILY":   {"K":  0.53, "G":  0.47},
    "CHJ_FAMILY":  {"CH": 0.52, "J":  0.48},
    "FV_FAMILY":   {"F":  0.53, "V":  0.47},
    "THDH_FAMILY": {"DH": 0.56, "TH": 0.44},  # DH > TH by frequency
    "SZ_FAMILY":   {"S":  0.62, "Z":  0.38},   # S significantly > Z
    "SHZH_FAMILY": {"SH": 0.54, "ZH": 0.46},
}


# ---------------------------------------------------------------------------
# Public scoring entry point
# ---------------------------------------------------------------------------

def compute_symbol_scores(
    features: StrokeFeatures,
    family: str,
) -> tuple[dict[str, float], bool, str | None]:
    """
    Return (scores, thickness_missing, reason).

    scores:            symbol → confidence value ∈ [0, THICKNESS_MISSING_CONFIDENCE_CAP]
    thickness_missing: True when pressure data was unavailable for this decision
    reason:            human-readable explanation (None when thickness IS available)

    Design contract:
        When features gains a pressure_stats field (future), add a block here:

            if features.pressure_stats is not None:
                return _score_from_pressure(features, family), False, None

        Everything else is unchanged — callers already handle thickness_missing=False.
    """
    if family not in FAMILY_SYMBOLS or family not in _FREQUENCY_PRIORS:
        return {}, True, f"No symbol data for family '{family}'"

    # Future pressure hook:
    # if getattr(features, "pressure_stats", None) is not None:
    #     return _score_from_pressure(features, family), False, None

    priors = _FREQUENCY_PRIORS[family]
    # Clamp all values to the confidence cap to be explicit about limitations.
    scores = {sym: min(conf, THICKNESS_MISSING_CONFIDENCE_CAP) for sym, conf in priors.items()}
    return scores, True, THICKNESS_MISSING_REASON


# ---------------------------------------------------------------------------
# Future: pressure-based scoring (stub — not called in M6)
# ---------------------------------------------------------------------------

def _score_from_pressure(
    features: StrokeFeatures,
    family: str,
) -> dict[str, float]:  # pragma: no cover
    """
    Placeholder for when pen pressure data becomes available.

    Expected input: features.pressure_stats.mean normalised to [0, 1]
      < 0.35 → light stroke → unvoiced symbol → high confidence
      > 0.65 → heavy stroke → voiced symbol   → high confidence
      0.35–0.65 → ambiguous → moderate confidence

    Returns scores with ceiling of 0.92 (allow for slight noise in pressure).
    """
    raise NotImplementedError(
        "Pressure scoring is not implemented until StrokeFeatures "
        "gains a pressure_stats field."
    )
