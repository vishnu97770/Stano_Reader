"""
Thresholds and scoring weights for hook detection.

All numeric constants live here so behaviour can be tuned without
touching detection logic.  Every constant is annotated with units and
the reasoning behind the chosen value.
"""

# ── Gate conditions — all must pass before zone analysis runs ───────────────

# Minimum total stroke length (CSS px) for hook detection.
# Shorter strokes have too few points to resolve the zone structure reliably.
HOOK_MIN_TOTAL_LENGTH_PX: float = 25.0

# Minimum point count.  Needed so the three zones each have >= 2 points.
# With HOOK_ZONE_FRACTION = 0.25: k = int(8 * 0.25) = 2, body = 4, total = 8.
HOOK_MIN_POINTS: int = 8

# Maximum curvature ratio (path_length / chord_length) for the overall stroke.
# A hook sits on a mostly straight body, so the total curvature should be low.
# Circles have curvature_ratio >= 2.5; we stay safely below that.
HOOK_MAX_CURVATURE: float = 2.0

# ── Zone sizes ───────────────────────────────────────────────────────────────

# Fraction of total points assigned to each endpoint zone.
# 0.25 means the initial and final zones each cover 25% of the stroke.
HOOK_ZONE_FRACTION: float = 0.25

# ── Angular thresholds ───────────────────────────────────────────────────────

# Minimum absolute deviation (degrees) from the body direction for a hook.
# Below this the deviation is indistinguishable from natural hand tremor.
HOOK_MIN_ANGLE_DEG: float = 20.0

# Maximum absolute deviation (degrees).
# Above this the deviation is a sharp bend or a different stroke type.
HOOK_MAX_ANGLE_DEG: float = 130.0

# Deviation angle at which the angle sub-score saturates (reaches 1.0).
# A 70° deviation is a very clear, pronounced hook.
HOOK_ANGLE_SATURATION_DEG: float = 70.0

# ── Hook length proportions ──────────────────────────────────────────────────

# Ideal hook-length-to-total-length ratio.
# In practice a hook occupies roughly 10–20% of the stroke.
HOOK_IDEAL_LENGTH_RATIO: float = 0.15

# Maximum hook length ratio.  Beyond this the "hook" is too large and is
# more likely a separate stroke element.
HOOK_MAX_LENGTH_RATIO: float = 0.40

# ── Confidence weights ───────────────────────────────────────────────────────

# How clearly the angular deviation exceeds the minimum threshold.
W_ANGLE: float = 0.50

# How well the hook-length ratio matches the ideal proportion.
W_LENGTH: float = 0.30

# How straight the stroke body is (curvature near 1.0 = perfectly straight).
W_BODY: float = 0.20
