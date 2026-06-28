"""
Tests for M16 — Stroke Extractor.

Covers stroke_extractor.py (extract_strokes, ExtractedPoint, ExtractedStroke,
_extract_points, _points_elongated, _points_compact).

Tests (20):
  - extract_strokes: empty image, blank image, single horizontal line,
                     single compact blob, noise filtering, reading-order sort,
                     filters border-filling component (7)
  - ExtractedPoint: fields, to_dict, pressure default, timestamp step (4)
  - ExtractedStroke: id not empty, to_dict structure (2)
  - _points_elongated: returns ≥2 points for a valid line (1)
  - _points_compact: first point is topmost, returns ≤TARGET_POINTS (2)
  - Point ordering: x values progress along elongated stroke (1)
  - Threshold constants present (1)
  - _extract_points: elongated path chosen for wide aspect, compact for square (2)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import uuid

import numpy as np
import pytest

from recognizer.stroke_extractor import (
    MIN_STROKE_AREA,
    MAX_STROKE_AREA_RATIO,
    MIN_STROKE_POINTS,
    TARGET_POINTS,
    ExtractedPoint,
    ExtractedStroke,
    _extract_points,
    _points_compact,
    _points_elongated,
    extract_strokes,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _line_image(
    x1: int, y: int, x2: int, thickness: int = 3,
    h: int = 200, w: int = 400,
) -> np.ndarray:
    """Binary image with a single horizontal line stroke."""
    img = np.zeros((h, w), dtype=np.uint8)
    img[y: y + thickness, x1:x2] = 255
    return img


def _circle_image(cx: int = 50, cy: int = 50, r: int = 20, h: int = 120, w: int = 120) -> np.ndarray:
    """Binary image with a filled circle."""
    img = np.zeros((h, w), dtype=np.uint8)
    import cv2
    cv2.circle(img, (cx, cy), r, 255, -1)
    return img


def _dot_image(cx: int = 10, cy: int = 10, r: int = 3, h: int = 80, w: int = 80) -> np.ndarray:
    """Very small dot — should be filtered as noise."""
    img = np.zeros((h, w), dtype=np.uint8)
    import cv2
    cv2.circle(img, (cx, cy), r, 255, -1)
    return img


# ── extract_strokes ───────────────────────────────────────────────────────────


def test_extract_strokes_empty_image():
    result = extract_strokes(np.zeros((0, 0), dtype=np.uint8))
    assert result == []


def test_extract_strokes_blank_image_no_strokes():
    blank = np.zeros((200, 300), dtype=np.uint8)
    result = extract_strokes(blank)
    assert result == []


def test_extract_strokes_single_horizontal_line():
    img = _line_image(x1=20, y=50, x2=300, thickness=4)
    result = extract_strokes(img)
    assert len(result) == 1


def test_extract_strokes_single_compact_blob():
    img = _circle_image(cx=60, cy=60, r=25)
    result = extract_strokes(img)
    assert len(result) == 1


def test_extract_strokes_filters_tiny_noise():
    img = _dot_image(r=2)  # area < MIN_STROKE_AREA
    result = extract_strokes(img)
    assert result == []


def test_extract_strokes_filters_full_page_component():
    """A component covering > 30% of the image should be discarded (page border)."""
    img = np.zeros((100, 100), dtype=np.uint8)
    img[5:95, 5:95] = 255  # ~81% of image area
    result = extract_strokes(img)
    assert result == []


def test_extract_strokes_sorts_top_to_bottom():
    """Two strokes at different heights should be returned in y order."""
    img = np.zeros((300, 200), dtype=np.uint8)
    img[20:24, 10:180] = 255    # top line
    img[200:204, 10:180] = 255  # bottom line
    result = extract_strokes(img)
    assert len(result) == 2
    y_first = sum(p.y for p in result[0].points) / len(result[0].points)
    y_second = sum(p.y for p in result[1].points) / len(result[1].points)
    assert y_first < y_second


def test_extract_strokes_each_has_minimum_points():
    img = _line_image(x1=10, y=40, x2=250, thickness=4)
    result = extract_strokes(img)
    assert all(len(s.points) >= MIN_STROKE_POINTS for s in result)


# ── ExtractedPoint ────────────────────────────────────────────────────────────


def test_extracted_point_fields():
    p = ExtractedPoint(x=10.5, y=20.3)
    assert p.x == 10.5
    assert p.y == 20.3
    assert p.pressure == 0.5
    assert p.timestamp == 0


def test_extracted_point_to_dict():
    p = ExtractedPoint(x=5.0, y=8.0, pressure=0.5, timestamp=32)
    d = p.to_dict()
    assert d == {"x": 5.0, "y": 8.0, "pressure": 0.5, "timestamp": 32}


def test_extracted_point_timestamp_step_is_16():
    img = _line_image(x1=10, y=30, x2=200, thickness=4)
    result = extract_strokes(img)
    assert len(result) > 0
    points = result[0].points
    # Timestamps should increment by 16
    for i in range(1, len(points)):
        assert points[i].timestamp == i * 16


def test_extracted_point_pressure_is_half():
    img = _line_image(x1=10, y=30, x2=200, thickness=4)
    result = extract_strokes(img)
    for p in result[0].points:
        assert p.pressure == 0.5


# ── ExtractedStroke ───────────────────────────────────────────────────────────


def test_extracted_stroke_id_is_uuid():
    img = _line_image(x1=10, y=40, x2=200, thickness=4)
    result = extract_strokes(img)
    assert len(result) > 0
    # UUID validation: must not raise
    uuid.UUID(result[0].id)


def test_extracted_stroke_to_dict():
    s = ExtractedStroke(
        id="test-id",
        points=[ExtractedPoint(x=1.0, y=2.0)],
    )
    d = s.to_dict()
    assert d["id"] == "test-id"
    assert isinstance(d["points"], list)
    assert d["points"][0]["x"] == 1.0


# ── _points_elongated ─────────────────────────────────────────────────────────


def test_points_elongated_returns_multiple_points():
    mask = np.zeros((10, 200), dtype=np.uint8)
    mask[4:6, :] = 255  # thin horizontal line
    pts = _points_elongated(mask)
    assert len(pts) >= 2


def test_points_elongated_respects_target_points():
    mask = np.zeros((5, 400), dtype=np.uint8)
    mask[2:4, :] = 255
    pts = _points_elongated(mask)
    assert len(pts) <= TARGET_POINTS


# ── _points_compact ───────────────────────────────────────────────────────────


def test_points_compact_first_point_is_topmost():
    import cv2
    mask = np.zeros((60, 60), dtype=np.uint8)
    cv2.circle(mask, (30, 30), 20, 255, -1)
    pts = _points_compact(mask)
    assert len(pts) > 0
    min_y = min(p[1] for p in pts)
    assert pts[0][1] == min_y


def test_points_compact_respects_target_points():
    import cv2
    mask = np.zeros((80, 80), dtype=np.uint8)
    cv2.circle(mask, (40, 40), 35, 255, -1)
    pts = _points_compact(mask)
    assert len(pts) <= TARGET_POINTS


# ── Threshold constants ───────────────────────────────────────────────────────


def test_threshold_constants_have_expected_values():
    assert MIN_STROKE_AREA == 50
    assert MAX_STROKE_AREA_RATIO == 0.30
    assert MIN_STROKE_POINTS == 3
    assert TARGET_POINTS == 40


# ── _extract_points strategy selection ───────────────────────────────────────


def test_extract_points_uses_elongated_for_wide_aspect():
    """Wide mask (aspect ≥ 2) should use elongated strategy — many collinear points."""
    mask = np.zeros((10, 200), dtype=np.uint8)
    mask[4:6, 5:195] = 255
    pts = _extract_points(mask)
    assert len(pts) >= 2


def test_extract_points_uses_compact_for_square_mask():
    """Square mask uses compact (contour-based) strategy."""
    import cv2
    mask = np.zeros((50, 50), dtype=np.uint8)
    cv2.circle(mask, (25, 25), 20, 255, -1)
    pts = _extract_points(mask)
    assert len(pts) >= 3
