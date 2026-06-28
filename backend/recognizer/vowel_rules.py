"""
Pure detection rule functions for Pitman vowel signs.

All functions are stateless and accept only plain numeric / dict inputs so
they can be tested without any framework dependencies.

Coordinate system (same as the rest of the recognizer):
  x increases left → right
  y increases top → bottom (canvas origin is top-left)
"""

import math
from dataclasses import dataclass

from recognizer.vowel_definitions import (
    DASH_MAX_PX,
    DOT_MAX_PX,
    PROXIMITY_PX,
    VOWEL_BY_KEY,
    VowelDefinition,
)


# ── Point helpers ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Point:
    x: float
    y: float


def _path_length(points: list[Point]) -> float:
    """Total Euclidean path length across all consecutive point pairs."""
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(points)):
        dx = points[i].x - points[i - 1].x
        dy = points[i].y - points[i - 1].y
        total += math.sqrt(dx * dx + dy * dy)
    return total


def _bounding_box(points: list[Point]) -> tuple[float, float, float, float]:
    """Return (min_x, max_x, min_y, max_y)."""
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    return min(xs), max(xs), min(ys), max(ys)


def _centroid(points: list[Point]) -> Point:
    n = len(points)
    if n == 0:
        return Point(0.0, 0.0)
    return Point(
        sum(p.x for p in points) / n,
        sum(p.y for p in points) / n,
    )


def _distance(a: Point, b: Point) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


# ── Mark classification ───────────────────────────────────────────────────────

def classify_mark(points: list[Point]) -> str | None:
    """
    Classify a stroke as "dot", "dash", or None (too large to be a vowel mark).

    Rules:
      dot  — bounding-box width AND height both < DOT_MAX_PX
      dash — path length ≥ DOT_MAX_PX and ≤ DASH_MAX_PX, with the bbox
             significantly longer in one dimension (aspect ratio ≥ 1.5)
      None — stroke is too large or too round to be a vowel mark
    """
    if len(points) < 1:
        return None

    min_x, max_x, min_y, max_y = _bounding_box(points)
    bbox_w = max_x - min_x
    bbox_h = max_y - min_y
    path_len = _path_length(points)

    # Dot: very small bounding box
    if bbox_w < DOT_MAX_PX and bbox_h < DOT_MAX_PX:
        return "dot"

    # Dash: short path length but elongated in one axis
    if path_len <= DASH_MAX_PX:
        long_axis = max(bbox_w, bbox_h)
        short_axis = min(bbox_w, bbox_h) if min(bbox_w, bbox_h) > 0 else 0.5
        if long_axis / short_axis >= 1.5:
            return "dash"

    return None


# ── Degree detection ──────────────────────────────────────────────────────────

def detect_degree(
    vowel_centroid: Point,
    consonant_start: Point,
    consonant_end: Point,
) -> int:
    """
    Determine the vowel degree (1, 2, or 3) by projecting the vowel centroid
    onto the consonant stroke and measuring the normalised parameter t ∈ [0, 1].

      t ∈ [0,   0.33) → degree 1  (near stroke start)
      t ∈ [0.33, 0.67) → degree 2  (near stroke middle)
      t ∈ [0.67, 1.0]  → degree 3  (near stroke end)

    When the consonant stroke is a point (zero length), degree 2 is returned.
    """
    dx = consonant_end.x - consonant_start.x
    dy = consonant_end.y - consonant_start.y
    seg_len_sq = dx * dx + dy * dy

    if seg_len_sq == 0.0:
        return 2  # degenerate stroke

    # Project vowel centroid onto the stroke direction
    vx = vowel_centroid.x - consonant_start.x
    vy = vowel_centroid.y - consonant_start.y
    t = (vx * dx + vy * dy) / seg_len_sq
    t = max(0.0, min(1.0, t))  # clamp to [0, 1]

    if t < 0.33:
        return 1
    if t < 0.67:
        return 2
    return 3


# ── Before/after detection ────────────────────────────────────────────────────

def detect_position(
    vowel_centroid: Point,
    consonant_start: Point,
    consonant_end: Point,
    consonant_centroid: Point,
) -> str:
    """
    Determine whether the vowel is 'before' or 'after' the consonant stroke.

    Strategy:
      Compute the signed area of the triangle formed by
      (consonant_start → consonant_end → vowel_centroid).  A positive value
      means the vowel is to the LEFT of the stroke direction (reading-order
      "before"); negative means to the RIGHT ("after").

    For purely horizontal consonants (or strokes that are nearly so) the
    sign convention reduces to above = before, below = after.

    Fallback (zero cross-product): uses the x-axis — left → before.
    """
    # Direction vector of the consonant stroke
    sdx = consonant_end.x - consonant_start.x
    sdy = consonant_end.y - consonant_start.y

    # Vector from consonant start to vowel centroid
    vdx = vowel_centroid.x - consonant_start.x
    vdy = vowel_centroid.y - consonant_start.y

    # 2-D cross product (z-component of sdx×vd)
    cross = sdx * vdy - sdy * vdx

    if cross > 0:
        return "before"
    if cross < 0:
        return "after"

    # Degenerate / collinear — fall back to simple x comparison
    return "before" if vowel_centroid.x <= consonant_centroid.x else "after"


# ── Proximity & nearest-consonant selection ───────────────────────────────────

@dataclass
class NearbyConsonant:
    stroke_id: str
    family: str
    centroid: Point
    start: Point
    end: Point


def find_nearest_consonant(
    vowel_centroid: Point,
    nearby: list[NearbyConsonant],
) -> NearbyConsonant | None:
    """
    Return the nearest consonant stroke whose centroid is within PROXIMITY_PX
    of the vowel centroid.  Returns None when no consonant is close enough.
    """
    best: NearbyConsonant | None = None
    best_dist = PROXIMITY_PX  # exclusive upper bound

    for consonant in nearby:
        d = _distance(vowel_centroid, consonant.centroid)
        if d < best_dist:
            best_dist = d
            best = consonant

    return best


# ── Full mark → VowelDefinition resolution ───────────────────────────────────

def resolve_vowel(
    points: list[Point],
    nearby: list[NearbyConsonant],
) -> tuple[VowelDefinition | None, NearbyConsonant | None, float, str]:
    """
    Given raw vowel-mark points and a list of nearby consonant descriptors,
    return (definition, nearest_consonant, confidence, reasoning).

    Returns (None, None, 0.0, reason_string) when the stroke is not a vowel or
    cannot be attached to a consonant.
    """
    mark = classify_mark(points)
    if mark is None:
        return None, None, 0.0, "Stroke too large or too round to be a Pitman vowel mark"

    centroid = _centroid(points)

    nearest = find_nearest_consonant(centroid, nearby)
    if nearest is None:
        if not nearby:
            return None, None, 0.0, "No nearby consonant strokes — cannot determine vowel attachment"
        return None, None, 0.0, (
            f"Nearest consonant is more than {PROXIMITY_PX:.0f}px away "
            "— vowel mark cannot be reliably attached"
        )

    degree = detect_degree(centroid, nearest.start, nearest.end)
    position = detect_position(centroid, nearest.start, nearest.end, nearest.centroid)

    key = (degree, position, mark)
    defn = VOWEL_BY_KEY.get(key)
    if defn is None:
        return None, nearest, 0.0, f"No vowel definition for key {key}"

    # Confidence is higher when the mark is unambiguously small and close
    path_len = _path_length(points)
    proximity = _distance(centroid, nearest.centroid)
    size_ratio = 1.0 - (path_len / DASH_MAX_PX if mark == "dash" else 0.0)
    proximity_ratio = 1.0 - (proximity / PROXIMITY_PX)
    confidence = round(0.6 * size_ratio + 0.4 * proximity_ratio, 4)
    confidence = max(0.0, min(1.0, confidence))

    reasoning = (
        f"{mark.upper()} mark detected; degree={degree} "
        f"({'near start' if degree == 1 else 'near middle' if degree == 2 else 'near end'} "
        f"of {nearest.stroke_id}); position={position}; "
        f"vowel={defn.symbol} ({defn.ipa}); example: '{defn.example}'"
    )
    return defn, nearest, confidence, reasoning
