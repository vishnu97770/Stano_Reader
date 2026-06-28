"""
Tests for M14 Task 7 changes:
  I-8  — alternatives field present on all M13x result schemas
  I-9  — detect_ aliases are callable and return identical results
  I-10 — /classify-position endpoint guard raised to < 2 points
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi import HTTPException

from app.api.position import classify_position_endpoint
from app.schemas.position import ClassifyPositionRequest
from app.schemas.stroke import StrokePointSchema
from recognizer.analyzer import analyze_stroke, detect_stroke
from recognizer.family_classifier import classify_stroke, detect_family
from recognizer.weight_classifier import classify_weight, detect_weight
from recognizer.schemas import (
    CircleResult,
    HookResult,
    LengthResult,
    PositionResult,
)


# ── I-8: alternatives field present on all M13x result schemas ────────────────

def test_circle_result_has_alternatives_field():
    assert hasattr(CircleResult.model_fields, "alternatives") or \
           "alternatives" in CircleResult.model_fields


def test_hook_result_has_alternatives_field():
    assert "alternatives" in HookResult.model_fields


def test_length_result_has_alternatives_field():
    assert "alternatives" in LengthResult.model_fields


def test_position_result_has_alternatives_field():
    assert "alternatives" in PositionResult.model_fields


def test_m13x_alternatives_default_to_empty_list():
    """All four M13x schemas must produce alternatives=[] when not set."""
    circle = CircleResult(
        stroke_id="s1", is_circle=False, circle_type=None,
        phoneme=None, confidence=0.0, word_position="ANY",
    )
    hook = HookResult(
        stroke_id="s1", is_hook=False, hook_type=None,
        attachment_position=None, phoneme=None, confidence=0.0,
    )
    length = LengthResult(
        stroke_id="s1", is_modified=False, modification_type=None,
        added_phoneme=None, confidence=0.0,
        canonical_length=90.0, measured_length=90.0, length_ratio=1.0,
    )
    position = PositionResult(
        stroke_id="s1", position="SECOND", confidence=0.9,
        centroid_y=300.0, normalized_y=0.5, canvas_height=600.0,
    )
    assert circle.alternatives == []
    assert hook.alternatives == []
    assert length.alternatives == []
    assert position.alternatives == []


# ── I-9: detect_ aliases are callable and return identical results ─────────────

def _make_points(n: int = 5) -> list[dict]:
    return [{"x": float(i * 10), "y": float(i * 5), "pressure": 0.5, "timestamp": i}
            for i in range(n)]


def test_detect_stroke_alias_exists():
    assert detect_stroke is analyze_stroke


def test_detect_stroke_returns_same_result_as_analyze_stroke():
    pts = _make_points(6)
    r1 = analyze_stroke("sid", pts)
    r2 = detect_stroke("sid", pts)
    assert r1.model_dump() == r2.model_dump()


def test_detect_family_alias_exists():
    assert detect_family is classify_stroke


def test_detect_family_returns_same_result_as_classify_stroke():
    pts = _make_points(8)
    features = analyze_stroke("sid", pts)
    r1 = classify_stroke(features)
    r2 = detect_family(features)
    assert r1.model_dump() == r2.model_dump()


def test_detect_weight_alias_exists():
    assert detect_weight is classify_weight


def test_detect_weight_returns_same_result_as_classify_weight():
    pts = [{"x": float(i), "y": 0.0, "pressure": 0.1, "timestamp": i} for i in range(5)]
    r1 = classify_weight("sid", pts)
    r2 = detect_weight("sid", pts)
    assert r1.model_dump() == r2.model_dump()


# ── I-10: /classify-position endpoint rejects fewer than 2 points ─────────────

def _make_point_schema(x: float = 0.0, y: float = 100.0) -> StrokePointSchema:
    return StrokePointSchema(x=x, y=y, pressure=0.5, timestamp=0)


def test_position_endpoint_rejects_single_point():
    """A request with exactly 1 point must raise HTTPException 422."""
    body = ClassifyPositionRequest(
        stroke_id="p-test",
        points=[_make_point_schema()],
        canvas_height=600.0,
    )
    with pytest.raises(HTTPException) as exc_info:
        classify_position_endpoint(body)
    assert exc_info.value.status_code == 422


def test_position_endpoint_rejects_empty_points():
    """A request with 0 points must also raise HTTPException 422."""
    body = ClassifyPositionRequest(
        stroke_id="p-test2",
        points=[],
        canvas_height=600.0,
    )
    with pytest.raises(HTTPException) as exc_info:
        classify_position_endpoint(body)
    assert exc_info.value.status_code == 422


def test_position_endpoint_accepts_two_points():
    """Exactly 2 points must pass the guard and return a PositionResult."""
    body = ClassifyPositionRequest(
        stroke_id="p-test3",
        points=[_make_point_schema(0.0, 100.0), _make_point_schema(10.0, 200.0)],
        canvas_height=600.0,
    )
    result = classify_position_endpoint(body)
    assert isinstance(result, PositionResult)
    assert result.stroke_id == "p-test3"
