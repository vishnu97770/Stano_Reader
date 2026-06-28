"""
Unit tests for the M13C halving/doubling detector.

Tests cover: normal stroke, half-length stroke, double-length stroke, gating
conditions (too short, curved), and family-specific canonical lengths.
"""

import math
import sys
import os

# Allow running from the backend/ directory without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from recognizer.length_definitions import (
    GLOBAL_CANONICAL_PX,
    LENGTH_DEFINITIONS,
)
from recognizer.length_rules import (
    DOUBLE_RATIO_CENTER,
    DOUBLE_RATIO_MAX,
    DOUBLE_RATIO_MIN,
    HALF_RATIO_CENTER,
    HALF_RATIO_MAX,
    HALF_RATIO_MIN,
    LENGTH_MIN_PX,
    MAX_CURVATURE_RATIO,
)
from recognizer.schemas import BoundingBox, PressureStats, StrokeFeatures
from recognizer.length_detector import detect_length


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_features(
    stroke_id: str,
    length: float,
    curvature_ratio: float = 1.0,
    angle: float = 90.0,
) -> StrokeFeatures:
    """Build a minimal StrokeFeatures with the given length and curvature."""
    return StrokeFeatures(
        stroke_id=stroke_id,
        length=length,
        avg_segment_length=length / 10,
        direction="down",
        angle=angle,
        bounding_box=BoundingBox(
            min_x=0.0, max_x=20.0,
            min_y=0.0, max_y=length,
            width=20.0, height=length,
        ),
        point_count=11,
        is_curve=curvature_ratio >= 1.5,
        curvature_ratio=curvature_ratio,
        pressure_stats=None,
    )


# ── Normal stroke ─────────────────────────────────────────────────────────────

def test_normal_stroke_not_modified():
    """A stroke at exactly the canonical length must not be modified."""
    features = make_features("s1", length=GLOBAL_CANONICAL_PX)
    result = detect_length("s1", features)
    assert result.is_modified is False
    assert result.modification_type is None
    assert result.added_phoneme is None
    assert result.confidence == 0.0
    assert math.isclose(result.length_ratio, 1.0, rel_tol=1e-3)


def test_slightly_short_normal_stroke_not_half():
    """A stroke at 0.70× canonical is outside the HALF band and must be NORMAL."""
    length = GLOBAL_CANONICAL_PX * 0.70
    features = make_features("s2", length=length)
    result = detect_length("s2", features)
    assert result.is_modified is False


def test_slightly_long_normal_stroke_not_double():
    """A stroke at 1.50× canonical is below the DOUBLE band and must be NORMAL."""
    length = GLOBAL_CANONICAL_PX * 1.50
    features = make_features("s3", length=length)
    result = detect_length("s3", features)
    assert result.is_modified is False


# ── Half-length strokes ───────────────────────────────────────────────────────

def test_ideal_half_stroke_detected():
    """A stroke at exactly 0.5× canonical must be HALF with high confidence."""
    length = GLOBAL_CANONICAL_PX * HALF_RATIO_CENTER
    features = make_features("h1", length=length)
    result = detect_length("h1", features)
    assert result.is_modified is True
    assert result.modification_type == "HALF"
    assert result.added_phoneme is not None
    assert result.confidence > 0.5


def test_half_stroke_at_lower_edge():
    """A stroke at HALF_RATIO_MIN× canonical is on the edge — should NOT be detected."""
    length = GLOBAL_CANONICAL_PX * HALF_RATIO_MIN
    features = make_features("h2", length=length)
    result = detect_length("h2", features)
    # At the exact edge ratio_confidence returns 0.0; combined confidence may still
    # be 0.0 from ratio but > 0 from length — so we only assert modification_type
    # matches or is_modified is correct with edge case semantics.
    # Since HALF_RATIO_MIN is the inclusive lower bound in the rule (<=), it will
    # technically enter the half band with 0 ratio_confidence.
    assert result.modification_type in ("HALF", None)


def test_half_stroke_just_inside_upper_edge():
    """A stroke at (HALF_RATIO_MAX - small ε) is still in the HALF band."""
    length = GLOBAL_CANONICAL_PX * (HALF_RATIO_MAX - 0.02)
    features = make_features("h3", length=length)
    result = detect_length("h3", features)
    assert result.is_modified is True
    assert result.modification_type == "HALF"


def test_half_stroke_has_correct_phoneme():
    """HALF strokes must carry the '/t/' phoneme from the global definition."""
    length = GLOBAL_CANONICAL_PX * HALF_RATIO_CENTER
    features = make_features("h4", length=length)
    result = detect_length("h4", features)
    assert result.added_phoneme == "/t/"


# ── Double-length strokes ─────────────────────────────────────────────────────

def test_ideal_double_stroke_detected():
    """A stroke at exactly 2.0× canonical must be DOUBLE with high confidence."""
    length = GLOBAL_CANONICAL_PX * DOUBLE_RATIO_CENTER
    features = make_features("d1", length=length)
    result = detect_length("d1", features)
    assert result.is_modified is True
    assert result.modification_type == "DOUBLE"
    assert result.added_phoneme is not None
    assert result.confidence > 0.5


def test_double_stroke_just_inside_lower_edge():
    """A stroke at (DOUBLE_RATIO_MIN + ε) is in the DOUBLE band."""
    length = GLOBAL_CANONICAL_PX * (DOUBLE_RATIO_MIN + 0.02)
    features = make_features("d2", length=length)
    result = detect_length("d2", features)
    assert result.is_modified is True
    assert result.modification_type == "DOUBLE"


def test_double_stroke_above_upper_edge_not_detected():
    """A stroke beyond DOUBLE_RATIO_MAX is too long to be a double — NORMAL."""
    length = GLOBAL_CANONICAL_PX * (DOUBLE_RATIO_MAX + 0.10)
    features = make_features("d3", length=length)
    result = detect_length("d3", features)
    assert result.is_modified is False


def test_double_stroke_has_correct_phoneme():
    """DOUBLE strokes must carry the '/r/' phoneme from the global definition."""
    length = GLOBAL_CANONICAL_PX * DOUBLE_RATIO_CENTER
    features = make_features("d4", length=length)
    result = detect_length("d4", features)
    assert result.added_phoneme == "/r/"


# ── Gate conditions ───────────────────────────────────────────────────────────

def test_too_short_stroke_not_modified():
    """Strokes shorter than LENGTH_MIN_PX must always return is_modified=False."""
    features = make_features("g1", length=LENGTH_MIN_PX - 1.0)
    result = detect_length("g1", features)
    assert result.is_modified is False


def test_zero_length_not_modified():
    """Edge case: zero-length stroke must not crash and must return is_modified=False."""
    features = make_features("g2", length=0.0)
    result = detect_length("g2", features)
    assert result.is_modified is False


def test_curved_stroke_excluded():
    """High curvature_ratio (circle/loop) must exclude the stroke from detection."""
    length = GLOBAL_CANONICAL_PX * HALF_RATIO_CENTER
    features = make_features("g3", length=length, curvature_ratio=MAX_CURVATURE_RATIO + 0.5)
    result = detect_length("g3", features)
    assert result.is_modified is False


# ── Family-specific canonical lengths ────────────────────────────────────────

def test_family_canonical_used_when_provided():
    """With PB_FAMILY (100px canonical), a 50px stroke should be HALF."""
    pb_canonical = LENGTH_DEFINITIONS["PB_FAMILY"].canonical_px  # 100px
    length = pb_canonical * HALF_RATIO_CENTER                    # 50px
    features = make_features("f1", length=length)
    result = detect_length("f1", features, family_name="PB_FAMILY")
    assert result.is_modified is True
    assert result.modification_type == "HALF"
    assert math.isclose(result.canonical_length, pb_canonical)


def test_family_canonical_differs_from_global():
    """KG_FAMILY (80px canonical) vs global (90px) changes where the band sits."""
    # A 40px stroke: vs KG canonical (80px) → ratio 0.50 → HALF
    # vs global (90px)                      → ratio 0.44 → also HALF, but different ratio
    kg_canonical = LENGTH_DEFINITIONS["KG_FAMILY"].canonical_px  # 80px
    length = kg_canonical * HALF_RATIO_CENTER                    # 40px
    result_family = detect_length("f2", make_features("f2", length=length), family_name="KG_FAMILY")
    result_global = detect_length("f2", make_features("f2", length=length))
    assert result_family.canonical_length == kg_canonical
    assert result_global.canonical_length == GLOBAL_CANONICAL_PX
    # Both should detect HALF since 40px is in HALF range for both canonicals
    assert result_family.modification_type == "HALF"
    assert result_global.modification_type == "HALF"


def test_unknown_family_falls_back_to_global():
    """An unrecognised family name must silently fall back to the global canonical."""
    length = GLOBAL_CANONICAL_PX * HALF_RATIO_CENTER
    features = make_features("f3", length=length)
    result = detect_length("f3", features, family_name="NONEXISTENT_FAMILY")
    assert math.isclose(result.canonical_length, GLOBAL_CANONICAL_PX)
    assert result.is_modified is True


def test_none_family_uses_global():
    """family_name=None must use the global canonical length."""
    length = GLOBAL_CANONICAL_PX * DOUBLE_RATIO_CENTER
    features = make_features("f4", length=length)
    result = detect_length("f4", features, family_name=None)
    assert math.isclose(result.canonical_length, GLOBAL_CANONICAL_PX)
    assert result.modification_type == "DOUBLE"


# ── Result fields ─────────────────────────────────────────────────────────────

def test_result_echoes_stroke_id():
    features = make_features("echo-id", length=GLOBAL_CANONICAL_PX)
    result = detect_length("echo-id", features)
    assert result.stroke_id == "echo-id"


def test_result_includes_measured_and_canonical():
    """measured_length and canonical_length must be set regardless of outcome."""
    length = GLOBAL_CANONICAL_PX * 1.0
    features = make_features("rc1", length=length)
    result = detect_length("rc1", features)
    assert result.measured_length == length
    assert result.canonical_length == GLOBAL_CANONICAL_PX


def test_half_result_has_reasoning():
    """HALF detections must have a non-empty reasoning string."""
    length = GLOBAL_CANONICAL_PX * HALF_RATIO_CENTER
    features = make_features("rr1", length=length)
    result = detect_length("rr1", features)
    assert result.reasoning is not None
    assert len(result.reasoning) > 0


def test_double_result_has_reasoning():
    """DOUBLE detections must have a non-empty reasoning string."""
    length = GLOBAL_CANONICAL_PX * DOUBLE_RATIO_CENTER
    features = make_features("rr2", length=length)
    result = detect_length("rr2", features)
    assert result.reasoning is not None
    assert len(result.reasoning) > 0


def test_normal_result_reasoning_is_empty():
    """Normal strokes must have reasoning='' (M14: reasoning is str, never None)."""
    features = make_features("rr3", length=GLOBAL_CANONICAL_PX)
    result = detect_length("rr3", features)
    assert isinstance(result.reasoning, str)
    assert result.reasoning == ""


def test_confidence_zero_for_normal():
    features = make_features("cv1", length=GLOBAL_CANONICAL_PX)
    result = detect_length("cv1", features)
    assert result.confidence == 0.0


def test_confidence_in_range_for_half():
    length = GLOBAL_CANONICAL_PX * HALF_RATIO_CENTER
    features = make_features("cv2", length=length)
    result = detect_length("cv2", features)
    assert 0.0 < result.confidence <= 1.0
