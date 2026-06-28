"""
Hook detector for Pitman shorthand.

Public interface
────────────────
    detect_hook(stroke_id, features, points) -> HookResult

Returns is_hook=False immediately when gate conditions (defined in
hook_rules.py) are not satisfied.  When they are, it compares the
direction of each endpoint zone against the body direction.  The
endpoint with the highest-confidence hook wins.

Feature reuse
─────────────
detect_hook() takes pre-computed StrokeFeatures so callers that already
ran analyze_stroke() do not pay for re-extraction.  Raw points are
required only for zone-level angle and length computation.

Zone model
──────────
    [ INITIAL zone | ──── BODY zone ──── | FINAL zone ]
      first k pts       middle pts          last k pts
    where k = max(2, int(N * HOOK_ZONE_FRACTION))

Deviation convention (rotationally invariant)
──────────────────────────────────────────────
    signed_diff = (zone_angle - body_angle) normalised to [-180, 180]

    INITIAL zone:
      positive signed_diff → hook is CCW from body → L Hook (/l/)
      negative signed_diff → hook is CW  from body → R Hook (/r/)

    FINAL zone:
      negative signed_diff → hook is CW  from body → N Hook   (/n/)
      positive signed_diff → hook is CCW from body → F/V Hook (/f/)

Future extensibility
────────────────────
Add large hooks, shun hook, or compound hooks by:
  1. Adding new entries to hook_definitions.py
  2. Adding a new branch in _classify_hook_type() below
  No change to the public interface or schema is needed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from recognizer.hook_definitions import HOOK_DEFINITIONS
from recognizer.hook_rules import (
    HOOK_ANGLE_SATURATION_DEG,
    HOOK_IDEAL_LENGTH_RATIO,
    HOOK_MAX_ANGLE_DEG,
    HOOK_MAX_CURVATURE,
    HOOK_MAX_LENGTH_RATIO,
    HOOK_MIN_ANGLE_DEG,
    HOOK_MIN_POINTS,
    HOOK_MIN_TOTAL_LENGTH_PX,
    HOOK_ZONE_FRACTION,
    W_ANGLE,
    W_BODY,
    W_LENGTH,
)
from recognizer.schemas import HookResult, StrokeFeatures


# ---------------------------------------------------------------------------
# Internal data class — not exposed outside this module
# ---------------------------------------------------------------------------

@dataclass
class _HookCandidate:
    hook_type: str     # e.g. "L_HOOK_INITIAL"
    position: str      # "INITIAL" | "FINAL"
    deviation_deg: float
    hook_ratio: float
    confidence: float


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _zone_size(n_points: int) -> int:
    return max(2, int(n_points * HOOK_ZONE_FRACTION))


def _point_angle(p1: dict, p2: dict) -> float | None:
    """Bearing from p1 to p2 in [0, 360). Returns None if points coincide."""
    dx = p2["x"] - p1["x"]
    dy = p2["y"] - p1["y"]
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return None
    return math.degrees(math.atan2(dy, dx)) % 360


def _zone_angle(zone_pts: list[dict]) -> float | None:
    """Bearing from the first to the last point in a zone."""
    if len(zone_pts) < 2:
        return None
    return _point_angle(zone_pts[0], zone_pts[-1])


def _zone_length(zone_pts: list[dict]) -> float:
    """Total path length of a zone."""
    total = 0.0
    for i in range(len(zone_pts) - 1):
        dx = zone_pts[i + 1]["x"] - zone_pts[i]["x"]
        dy = zone_pts[i + 1]["y"] - zone_pts[i]["y"]
        total += math.sqrt(dx * dx + dy * dy)
    return total


def _signed_diff(from_deg: float, to_deg: float) -> float:
    """Signed angular difference (to_deg - from_deg), normalised to [-180, 180]."""
    diff = (to_deg - from_deg) % 360
    if diff > 180:
        diff -= 360
    return diff


# ---------------------------------------------------------------------------
# Hook type classification
# ---------------------------------------------------------------------------

def _classify_hook_type(position: str, deviation: float) -> str:
    """
    Determine the hook name from position and the sign of the deviation.

    INITIAL hooks:
      deviation > 0 → L Hook (zone is CCW / left of body)
      deviation < 0 → R Hook (zone is CW / right of body)

    FINAL hooks:
      deviation < 0 → N Hook (zone is CW / right of body)
      deviation > 0 → F/V Hook (zone is CCW / left of body)

    For future large hooks or compound hooks, add branches here keyed on
    additional parameters (e.g. size, absolute angle range).
    """
    if position == "INITIAL":
        return "L_HOOK_INITIAL" if deviation > 0 else "R_HOOK_INITIAL"
    else:
        return "N_HOOK_FINAL" if deviation < 0 else "FV_HOOK_FINAL"


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

def _angle_conf(deviation_deg: float) -> float:
    """Score in [0, 1] based on how pronounced the angular deviation is."""
    span = HOOK_ANGLE_SATURATION_DEG - HOOK_MIN_ANGLE_DEG
    return min(1.0, (deviation_deg - HOOK_MIN_ANGLE_DEG) / span)


def _length_conf(ratio: float) -> float:
    """Score in [0, 1] based on how well the hook-length ratio fits the ideal."""
    if ratio < 0.03 or ratio > HOOK_MAX_LENGTH_RATIO:
        return 0.0
    ideal = HOOK_IDEAL_LENGTH_RATIO
    # Max distance from ideal to either boundary
    max_dist = max(ideal - 0.03, HOOK_MAX_LENGTH_RATIO - ideal)
    return max(0.0, 1.0 - abs(ratio - ideal) / max_dist)


def _body_conf(features: StrokeFeatures) -> float:
    """Score in [0, 1] based on body straightness (curvature_ratio close to 1.0)."""
    return max(0.0, 1.0 - (features.curvature_ratio - 1.0) / (HOOK_MAX_CURVATURE - 1.0))


# ---------------------------------------------------------------------------
# Gate check
# ---------------------------------------------------------------------------

def _passes_gate(features: StrokeFeatures) -> bool:
    if features.point_count < HOOK_MIN_POINTS:
        return False
    if features.length < HOOK_MIN_TOTAL_LENGTH_PX:
        return False
    if features.curvature_ratio > HOOK_MAX_CURVATURE:
        return False
    return True


# ---------------------------------------------------------------------------
# Zone analysis
# ---------------------------------------------------------------------------

def _analyse_zone(
    zone_pts: list[dict],
    body_angle: float,
    total_length: float,
    position: str,
    features: StrokeFeatures,
) -> _HookCandidate | None:
    """
    Check one endpoint zone for a hook against the body direction.
    Returns a _HookCandidate if the zone passes the angular threshold,
    or None if the zone does not qualify.
    """
    zone_ang = _zone_angle(zone_pts)
    if zone_ang is None:
        return None

    signed = _signed_diff(body_angle, zone_ang)
    abs_dev = abs(signed)

    if abs_dev < HOOK_MIN_ANGLE_DEG or abs_dev > HOOK_MAX_ANGLE_DEG:
        return None

    hook_len = _zone_length(zone_pts)
    if total_length < 1e-9:
        return None
    ratio = hook_len / total_length

    hook_type = _classify_hook_type(position, signed)
    angle_c = _angle_conf(abs_dev)
    length_c = _length_conf(ratio)
    body_c = _body_conf(features)

    confidence = round(W_ANGLE * angle_c + W_LENGTH * length_c + W_BODY * body_c, 4)

    return _HookCandidate(
        hook_type=hook_type,
        position=position,
        deviation_deg=abs_dev,
        hook_ratio=ratio,
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def detect_hook(
    stroke_id: str,
    features: StrokeFeatures,
    points: list[dict],
) -> HookResult:
    """
    Classify a stroke as containing a hook, or return is_hook=False.

    Args:
        stroke_id: UUID echoed into the result.
        features:  Pre-computed StrokeFeatures (from analyze_stroke).
        points:    Raw point list for zone-level angle and length computation.

    Returns:
        HookResult.  is_hook=False when gate conditions are not met or no
        zone exceeds the angular threshold.
    """
    def _not_hook() -> HookResult:
        return HookResult(
            stroke_id=stroke_id,
            is_hook=False,
            hook_type=None,
            position=None,
            phoneme=None,
            confidence=0.0,
            reasoning=None,
        )

    if not _passes_gate(features):
        return _not_hook()

    n = len(points)
    k = _zone_size(n)

    initial_zone = points[:k]
    body_zone = points[k : n - k]
    final_zone = points[n - k :]

    # Body direction: use middle zone to avoid endpoint bias
    body_angle = _zone_angle(body_zone)
    if body_angle is None:
        # Fall back to full-stroke angle when body zone is degenerate
        body_angle = features.angle

    candidates: list[_HookCandidate] = []

    initial_cand = _analyse_zone(
        initial_zone, body_angle, features.length, "INITIAL", features
    )
    if initial_cand is not None:
        candidates.append(initial_cand)

    final_cand = _analyse_zone(
        final_zone, body_angle, features.length, "FINAL", features
    )
    if final_cand is not None:
        candidates.append(final_cand)

    if not candidates:
        return _not_hook()

    # Choose the candidate with the highest confidence
    best = max(candidates, key=lambda c: c.confidence)
    defn = HOOK_DEFINITIONS[best.hook_type]

    reasoning = (
        f"{best.hook_type}: deviation={best.deviation_deg:.1f}°, "
        f"hook_ratio={best.hook_ratio:.2f}, "
        f"conf={best.confidence:.3f}"
    )

    return HookResult(
        stroke_id=stroke_id,
        is_hook=True,
        hook_type=best.hook_type,
        position=best.position,
        phoneme=defn.phoneme,
        confidence=best.confidence,
        reasoning=reasoning,
    )
