"""
Threshold constants and pure functions for position detection.

Canvas coordinate system: Y=0 is the top; Y=canvas_height is the bottom.
All Y fractions are normalized to [0, 1] by dividing by canvas_height.

Band layout (equal thirds):
    [0.000, 0.333)  → FIRST
    [0.333, 0.667]  → SECOND
    (0.667, 1.000]  → THIRD

Confidence degrades linearly near inter-zone boundaries.
Outer canvas edges (top/bottom) carry no penalty — strokes there are
unambiguously in FIRST or THIRD position respectively.
"""

# ── Guard ─────────────────────────────────────────────────────────────────────

# Canvas heights below this are treated as invalid
MIN_CANVAS_HEIGHT_PX: float = 10.0

# ── Virtual line fractions (normalized to canvas height) ───────────────────────
LINE1_FRACTION: float = 1.0 / 3.0   # FIRST / SECOND boundary
LINE2_FRACTION: float = 2.0 / 3.0   # SECOND / THIRD boundary

# ── Confidence ────────────────────────────────────────────────────────────────

# Width of the transition corridor at each inter-zone boundary.
# Confidence ramps from 0.0 (at boundary) to 1.0 (at TRANSITION_WIDTH into the band).
TRANSITION_WIDTH: float = 0.10


def compute_centroid_y(points: list[dict]) -> float:
    """Return the mean Y coordinate of all stroke points."""
    return sum(p["y"] for p in points) / len(points)


def classify_band(norm_y: float) -> str:
    """
    Return the writing position for a normalized Y value in [0, 1].

    Boundaries are SECOND-inclusive so that a stroke exactly on a guide
    line classifies as the more common middle position.
    """
    if norm_y < LINE1_FRACTION:
        return "FIRST"
    elif norm_y <= LINE2_FRACTION:
        return "SECOND"
    else:
        return "THIRD"


def position_confidence(norm_y: float, band: str) -> float:
    """
    Confidence based on distance from the nearest inter-zone boundary.

    - 1.0  when the centroid is >= TRANSITION_WIDTH inside the band
    - 0.0  exactly at the boundary
    - Outer edges (Y=0 for FIRST, Y=1 for THIRD) carry no penalty
    """
    if band == "FIRST":
        margin = LINE1_FRACTION - norm_y
    elif band == "THIRD":
        margin = norm_y - LINE2_FRACTION
    else:  # SECOND
        margin = min(norm_y - LINE1_FRACTION, LINE2_FRACTION - norm_y)

    return round(min(1.0, max(0.0, margin / TRANSITION_WIDTH)), 3)
