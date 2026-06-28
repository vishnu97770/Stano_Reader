"""
Unit tests for the M13D writing position detector.

Tests cover: all three positions, boundary conditions, transition zone
confidence, invalid canvas height, centroid computation, and result fields.
"""

import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from recognizer.position_rules import (
    LINE1_FRACTION,
    LINE2_FRACTION,
    MIN_CANVAS_HEIGHT_PX,
    TRANSITION_WIDTH,
    classify_band,
    compute_centroid_y,
    position_confidence,
)
from recognizer.position_detector import detect_position


# ── Helpers ──────────────────────────────────────────────────────────────────

CANVAS_H = 600.0  # standard canvas height for all tests unless stated


def pts(y: float, n: int = 5) -> list[dict]:
    """Return n points all at the same Y, spread across X."""
    return [{"x": float(i * 10), "y": y} for i in range(n)]


def pts_varying(ys: list[float]) -> list[dict]:
    """Return points with the given Y values."""
    return [{"x": float(i), "y": y} for i, y in enumerate(ys)]


# ── First position ────────────────────────────────────────────────────────────

def test_first_position_center():
    """Centroid at exactly the center of the FIRST band → FIRST, high confidence."""
    cy = CANVAS_H * (LINE1_FRACTION / 2.0)   # 0.167 normalized
    result = detect_position("s1", pts(cy), CANVAS_H)
    assert result.position == "FIRST"
    assert result.confidence >= 0.9


def test_first_position_top_edge():
    """Centroid at Y=1 (very top) → FIRST with full confidence (outer edge not penalized)."""
    result = detect_position("s2", pts(1.0), CANVAS_H)
    assert result.position == "FIRST"
    assert result.confidence == 1.0


def test_first_position_y_zero():
    """Centroid at exactly Y=0 → FIRST, full confidence."""
    result = detect_position("s3", pts(0.0), CANVAS_H)
    assert result.position == "FIRST"
    assert result.confidence == 1.0


# ── Second position ───────────────────────────────────────────────────────────

def test_second_position_center():
    """Centroid at canvas midpoint → SECOND, high confidence."""
    result = detect_position("s4", pts(CANVAS_H * 0.5), CANVAS_H)
    assert result.position == "SECOND"
    assert result.confidence == 1.0


def test_second_position_at_line1_exact():
    """Centroid exactly on LINE1 boundary → SECOND (boundary is SECOND-inclusive)."""
    cy = CANVAS_H * LINE1_FRACTION
    result = detect_position("s5", pts(cy), CANVAS_H)
    assert result.position == "SECOND"
    assert result.confidence == 0.0   # exactly at boundary → zero confidence


def test_second_position_at_line2_exact():
    """Centroid exactly on LINE2 boundary → SECOND (boundary is SECOND-inclusive)."""
    cy = CANVAS_H * LINE2_FRACTION
    result = detect_position("s6", pts(cy), CANVAS_H)
    assert result.position == "SECOND"
    assert result.confidence == 0.0


# ── Third position ────────────────────────────────────────────────────────────

def test_third_position_center():
    """Centroid at center of THIRD band → THIRD, high confidence."""
    cy = CANVAS_H * ((LINE2_FRACTION + 1.0) / 2.0)   # 0.833 normalized
    result = detect_position("s7", pts(cy), CANVAS_H)
    assert result.position == "THIRD"
    assert result.confidence >= 0.9


def test_third_position_bottom_edge():
    """Centroid at canvas bottom → THIRD, full confidence."""
    result = detect_position("s8", pts(CANVAS_H), CANVAS_H)
    assert result.position == "THIRD"
    assert result.confidence == 1.0


def test_third_position_just_past_line2():
    """Centroid just below LINE2 boundary → THIRD."""
    cy = CANVAS_H * (LINE2_FRACTION + 0.01)
    result = detect_position("s9", pts(cy), CANVAS_H)
    assert result.position == "THIRD"


# ── Boundary conditions ───────────────────────────────────────────────────────

def test_just_below_line1_boundary_is_first():
    """Centroid just above LINE1 → FIRST."""
    cy = CANVAS_H * (LINE1_FRACTION - 0.01)
    result = detect_position("b1", pts(cy), CANVAS_H)
    assert result.position == "FIRST"


def test_just_above_line2_boundary_is_third():
    """Centroid just below LINE2 → THIRD."""
    cy = CANVAS_H * (LINE2_FRACTION + 0.01)
    result = detect_position("b2", pts(cy), CANVAS_H)
    assert result.position == "THIRD"


def test_transition_zone_first_low_confidence():
    """Centroid within TRANSITION_WIDTH of LINE1 from the FIRST side → low confidence."""
    cy = CANVAS_H * (LINE1_FRACTION - TRANSITION_WIDTH / 2.0)
    result = detect_position("b3", pts(cy), CANVAS_H)
    assert result.position == "FIRST"
    assert result.confidence < 0.6


def test_transition_zone_second_lower_bound_low_confidence():
    """Centroid within TRANSITION_WIDTH of LINE1 from the SECOND side → low confidence."""
    cy = CANVAS_H * (LINE1_FRACTION + TRANSITION_WIDTH / 2.0)
    result = detect_position("b4", pts(cy), CANVAS_H)
    assert result.position == "SECOND"
    assert result.confidence < 0.6


def test_transition_zone_second_upper_bound_low_confidence():
    """Centroid within TRANSITION_WIDTH of LINE2 from the SECOND side → low confidence."""
    cy = CANVAS_H * (LINE2_FRACTION - TRANSITION_WIDTH / 2.0)
    result = detect_position("b5", pts(cy), CANVAS_H)
    assert result.position == "SECOND"
    assert result.confidence < 0.6


def test_transition_zone_third_low_confidence():
    """Centroid within TRANSITION_WIDTH of LINE2 from the THIRD side → low confidence."""
    cy = CANVAS_H * (LINE2_FRACTION + TRANSITION_WIDTH / 2.0)
    result = detect_position("b6", pts(cy), CANVAS_H)
    assert result.position == "THIRD"
    assert result.confidence < 0.6


def test_full_confidence_deep_in_first():
    """Centroid well inside FIRST band → confidence 1.0."""
    cy = CANVAS_H * 0.05   # very close to top
    result = detect_position("b7", pts(cy), CANVAS_H)
    assert result.position == "FIRST"
    assert result.confidence == 1.0


def test_full_confidence_deep_in_third():
    """Centroid well inside THIRD band → confidence 1.0."""
    cy = CANVAS_H * 0.95
    result = detect_position("b8", pts(cy), CANVAS_H)
    assert result.position == "THIRD"
    assert result.confidence == 1.0


# ── Invalid canvas height ─────────────────────────────────────────────────────

def test_canvas_height_zero_returns_unknown():
    result = detect_position("g1", pts(100.0), 0.0)
    assert result.position == "UNKNOWN"
    assert result.confidence == 0.0


def test_canvas_height_negative_returns_unknown():
    result = detect_position("g2", pts(100.0), -50.0)
    assert result.position == "UNKNOWN"
    assert result.confidence == 0.0


def test_canvas_height_below_min_returns_unknown():
    result = detect_position("g3", pts(5.0), MIN_CANVAS_HEIGHT_PX - 1.0)
    assert result.position == "UNKNOWN"


def test_empty_points_returns_unknown():
    result = detect_position("g4", [], CANVAS_H)
    assert result.position == "UNKNOWN"


# ── Centroid calculation ──────────────────────────────────────────────────────

def test_centroid_is_mean_of_y():
    """Centroid Y must equal the arithmetic mean of all point Y values."""
    y_values = [100.0, 200.0, 300.0]
    result = detect_position("c1", pts_varying(y_values), CANVAS_H)
    expected_centroid = sum(y_values) / len(y_values)
    assert math.isclose(result.centroid_y, expected_centroid, rel_tol=1e-4)


def test_normalized_y_equals_centroid_over_height():
    cy = 250.0
    result = detect_position("c2", pts(cy), CANVAS_H)
    expected_norm = cy / CANVAS_H
    assert math.isclose(result.normalized_y, expected_norm, rel_tol=1e-3)


def test_single_point_uses_its_y():
    """A stroke with only one point should use that point's Y as centroid."""
    result = detect_position("c3", [{"x": 0.0, "y": 500.0}], CANVAS_H)
    assert math.isclose(result.centroid_y, 500.0)
    assert result.position == "THIRD"


def test_out_of_bounds_y_clamped():
    """Points beyond the canvas bottom should not crash; result is clamped to THIRD."""
    result = detect_position("c4", pts(CANVAS_H * 1.5), CANVAS_H)
    assert result.position == "THIRD"
    assert result.normalized_y == 1.0


# ── Result fields ─────────────────────────────────────────────────────────────

def test_stroke_id_echoed():
    result = detect_position("my-id-123", pts(CANVAS_H * 0.5), CANVAS_H)
    assert result.stroke_id == "my-id-123"


def test_canvas_height_echoed():
    result = detect_position("r1", pts(CANVAS_H * 0.5), CANVAS_H)
    assert result.canvas_height == CANVAS_H


def test_reasoning_always_present():
    """PositionResult must always have a non-empty reasoning string."""
    for y_frac in [0.1, 0.5, 0.9]:
        result = detect_position("r2", pts(CANVAS_H * y_frac), CANVAS_H)
        assert result.reasoning is not None
        assert len(result.reasoning) > 0


def test_unknown_reasoning_present():
    """Even UNKNOWN results must have a reasoning string."""
    result = detect_position("r3", pts(100.0), 0.0)
    assert result.reasoning is not None
    assert len(result.reasoning) > 0


def test_confidence_in_range():
    """Confidence must always be in [0, 1]."""
    for y_frac in [0.0, 0.1, 0.333, 0.5, 0.667, 0.9, 1.0]:
        result = detect_position("range", pts(CANVAS_H * y_frac), CANVAS_H)
        assert 0.0 <= result.confidence <= 1.0, f"confidence out of range at y_frac={y_frac}"


# ── Pure function unit tests ──────────────────────────────────────────────────

def test_classify_band_first():
    assert classify_band(0.0) == "FIRST"
    assert classify_band(0.1) == "FIRST"
    assert classify_band(LINE1_FRACTION - 0.001) == "FIRST"


def test_classify_band_second():
    assert classify_band(LINE1_FRACTION) == "SECOND"
    assert classify_band(0.5) == "SECOND"
    assert classify_band(LINE2_FRACTION) == "SECOND"


def test_classify_band_third():
    assert classify_band(LINE2_FRACTION + 0.001) == "THIRD"
    assert classify_band(0.9) == "THIRD"
    assert classify_band(1.0) == "THIRD"


def test_compute_centroid_y_equal_weights():
    points = [{"x": 0.0, "y": 100.0}, {"x": 0.0, "y": 300.0}]
    assert compute_centroid_y(points) == 200.0


def test_position_confidence_zero_at_boundaries():
    assert position_confidence(LINE1_FRACTION, "FIRST") == 0.0
    assert position_confidence(LINE1_FRACTION, "SECOND") == 0.0
    assert position_confidence(LINE2_FRACTION, "SECOND") == 0.0
    assert position_confidence(LINE2_FRACTION, "THIRD") == 0.0


def test_position_confidence_full_away_from_boundary():
    assert position_confidence(0.0, "FIRST") == 1.0
    assert position_confidence(0.5, "SECOND") == 1.0
    assert position_confidence(1.0, "THIRD") == 1.0
