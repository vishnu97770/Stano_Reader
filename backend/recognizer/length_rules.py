"""
Threshold constants and confidence functions for halving/doubling detection.

Ratio = measured_length / canonical_length

HALF band  : [HALF_RATIO_MIN,   HALF_RATIO_MAX]   centred on 0.5
DOUBLE band: [DOUBLE_RATIO_MIN, DOUBLE_RATIO_MAX]  centred on 2.0

Confidence is linear within each band: 1.0 at the ideal centre, 0.0 at
each edge.  The weight constants scale the contribution of each metric to
the final confidence score.
"""

# ── Gate thresholds ───────────────────────────────────────────────────────────

# Strokes shorter than this cannot be reliably measured
LENGTH_MIN_PX: float = 20.0

# Curved strokes (circles, loops) are excluded from halving/doubling
MAX_CURVATURE_RATIO: float = 1.8

# ── Half-stroke band ─────────────────────────────────────────────────────────
HALF_RATIO_CENTER: float = 0.50
HALF_RATIO_MIN: float    = 0.30   # below this → too short to be intentional halving
HALF_RATIO_MAX: float    = 0.65   # above this → too long to be a half-stroke

# ── Double-stroke band ───────────────────────────────────────────────────────
DOUBLE_RATIO_CENTER: float = 2.00
DOUBLE_RATIO_MIN: float    = 1.65  # below this → might just be a long normal stroke
DOUBLE_RATIO_MAX: float    = 2.40  # above this → suspiciously long

# ── Confidence weights ────────────────────────────────────────────────────────
# Two signals contribute: ratio quality and stroke length (longer strokes
# are measured more reliably than very short ones).
W_RATIO: float  = 0.75
W_LENGTH: float = 0.25

# Minimum length confidence is capped once length exceeds this value (px)
LENGTH_CONFIDENCE_SATURATION_PX: float = 80.0


def ratio_confidence(ratio: float, center: float, low: float, high: float) -> float:
    """Linear confidence: 1.0 at center, 0.0 at the edges of [low, high]."""
    if ratio <= low or ratio >= high:
        return 0.0
    if ratio <= center:
        return (ratio - low) / (center - low)
    return (high - ratio) / (high - center)


def length_confidence(measured_px: float) -> float:
    """Longer strokes have better-sampled lengths; confidence saturates at 80px."""
    if measured_px <= 0:
        return 0.0
    return min(1.0, measured_px / LENGTH_CONFIDENCE_SATURATION_PX)
