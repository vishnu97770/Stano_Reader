"""
Pure geometric feature extraction functions.
All functions take plain dicts with keys {x, y, timestamp} and return primitives.
No I/O, no Pydantic, no FastAPI — fully testable in isolation.

Canvas coordinate system: Y increases downward, X increases rightward.
Angles follow atan2(dy, dx) convention: 0°=right, 90°=down, 180°=left, 270°=up.
"""

import math
from typing import TypedDict


class Point(TypedDict):
    x: float
    y: float
    timestamp: int


# ---------------------------------------------------------------------------
# Length
# ---------------------------------------------------------------------------

def compute_length(points: list[Point]) -> tuple[float, float]:
    """
    Returns (total_path_length, avg_segment_length).
    Both values are in the same unit as the input coordinates (CSS pixels).
    """
    if len(points) < 2:
        return 0.0, 0.0
    segments = [_dist(points[i], points[i + 1]) for i in range(len(points) - 1)]
    total = sum(segments)
    return total, total / len(segments)


# ---------------------------------------------------------------------------
# Direction and Angle
# ---------------------------------------------------------------------------

def compute_angle_and_direction(points: list[Point]) -> tuple[str, float]:
    """
    Returns (direction_label, angle_degrees).

    angle_degrees: start-to-end bearing in [0, 360).
      0   = rightward
      90  = downward  (canvas Y increases down)
      180 = leftward
      270 = upward

    direction_label: one of the 8 compass labels most aligned with the bearing.
    """
    if len(points) < 2:
        return "none", 0.0

    first, last = points[0], points[-1]
    dx = last["x"] - first["x"]
    dy = last["y"] - first["y"]

    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return "none", 0.0

    angle_deg = math.degrees(math.atan2(dy, dx)) % 360
    return _angle_to_direction(angle_deg), round(angle_deg, 2)


def _angle_to_direction(deg: float) -> str:
    """
    Maps a bearing in [0, 360) to one of 8 compass labels.
    Each label covers a 45° sector centered on its canonical bearing.
    """
    sectors = [
        (22.5,  "right"),
        (67.5,  "down-right"),
        (112.5, "down"),
        (157.5, "down-left"),
        (202.5, "left"),
        (247.5, "up-left"),
        (292.5, "up"),
        (337.5, "up-right"),
    ]
    for threshold, label in sectors:
        if deg < threshold:
            return label
    return "right"  # 337.5 – 360 wraps back to rightward


# ---------------------------------------------------------------------------
# Bounding Box
# ---------------------------------------------------------------------------

def compute_bounding_box(points: list[Point]) -> dict:
    """Returns a dict with min_x, max_x, min_y, max_y, width, height."""
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return {
        "min_x": round(min_x, 2),
        "max_x": round(max_x, 2),
        "min_y": round(min_y, 2),
        "max_y": round(max_y, 2),
        "width":  round(max_x - min_x, 2),
        "height": round(max_y - min_y, 2),
    }


# ---------------------------------------------------------------------------
# Curve Detection
# ---------------------------------------------------------------------------

def compute_curve(points: list[Point]) -> tuple[bool, float]:
    """
    Returns (is_curve, curvature_ratio).

    curvature_ratio = path_length / chord_length:
      ≈ 1.0  → straight stroke
      > 1.15 → gently curved
      > 1.57 → semicircular (π/2 ≈ 1.57)

    is_curve is True when either:
      1. curvature_ratio > 1.15  (path is ≥15% longer than the chord), OR
      2. max perpendicular deviation > 10% of chord length.

    Two independent heuristics are used so that short strokes with high
    angular deviation (which inflate the ratio less) still register as curves.
    """
    if len(points) < 3:
        return False, 1.0

    first, last = points[0], points[-1]
    chord = _dist(first, last)
    path_total, _ = compute_length(points)

    if chord < 1e-9:
        # Stroke loops back to its starting point — definitely a curve.
        return True, 0.0 if path_total == 0 else float("inf")

    ratio = path_total / chord

    # Secondary: maximum perpendicular deviation of any interior point.
    max_dev = _max_perp_deviation(points[1:-1], first, last, chord)
    deviation_curved = max_dev > 0.1 * chord

    return (ratio > 1.15 or deviation_curved), round(ratio, 4)


def _max_perp_deviation(
    interior: list[Point], first: Point, last: Point, chord: float
) -> float:
    """
    Maximum perpendicular distance from any interior point to the chord.
    Uses the cross-product formula: |AB × AP| / |AB|.
    """
    ax, ay = first["x"], first["y"]
    bx, by = last["x"],  last["y"]
    max_d = 0.0
    for p in interior:
        # |cross product (B-A) × (P-A)| / |AB|
        cross = abs((bx - ax) * (p["y"] - ay) - (by - ay) * (p["x"] - ax))
        d = cross / chord
        if d > max_d:
            max_d = d
    return max_d


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _dist(a: Point, b: Point) -> float:
    return math.sqrt((b["x"] - a["x"]) ** 2 + (b["y"] - a["y"]) ** 2)
