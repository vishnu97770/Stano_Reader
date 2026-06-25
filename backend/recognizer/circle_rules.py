"""
Thresholds and scoring weights for circle and loop detection.

All numeric constants live here so they can be adjusted without touching
detection logic.  Every constant is annotated with the unit and reasoning.
"""

# ── Gate conditions (all must pass for a stroke to be a circle candidate) ──

# Minimum curvature ratio (path_length / chord_length) for a circle candidate.
# A semicircle has ratio ≈ π/2 ≈ 1.57; a full circle has ratio → ∞.
# 2.5 filters out gently curved strokes while accepting clear circles/loops.
CIRCLE_MIN_CURVATURE: float = 2.5

# Maximum closure ratio (dist(first, last) / path_length).
# 0 = perfect closed loop; 1 = fully open stroke.
# 0.35 means the end point must be within 35% of the path length from the start.
CIRCLE_MAX_CLOSURE: float = 0.35

# Minimum bounding box area (CSS px²) to reject accidental dots or micro-strokes.
# 400 px² ≈ a 20×20 px square.
CIRCLE_MIN_AREA: float = 400.0

# ── Shape classification ────────────────────────────────────────────────────

# Elongation threshold that separates circles from loops.
# elongation = max(bbox_width, bbox_height) / min(bbox_width, bbox_height).
# Elongation < 2.0 → circle; elongation ≥ 2.0 → loop.
LOOP_ASPECT_THRESHOLD: float = 2.0

# ── Size classification ─────────────────────────────────────────────────────

# Bounding box area (px²) separating small from large circles/loops.
# 2500 px² ≈ a 50×50 px bounding box.
SMALL_SIZE_THRESHOLD_AREA: float = 2500.0

# ── Confidence scoring weights ──────────────────────────────────────────────

# Curvature score weight: how circular/closed the path is.
W_CURVATURE: float = 0.40

# Closure score weight: how well the stroke returns to its start.
W_CLOSURE: float = 0.40

# Type classification confidence weight: how clearly it fits the chosen type.
W_TYPE: float = 0.20

# Upper bound of curvature_ratio used in confidence normalisation.
# Curvature_ratio = 6.0 corresponds to a near-perfect circle (just over one
# full revolution).  Ratios above this saturate at confidence = 1.0.
CURVATURE_SATURATION: float = 6.0
