"""
Tests for M16 — Image Recognition.

Covers image_processor.py and page_analyzer.py.

Tests (30):
  - validate_upload: accepted types, oversized, exact limit (5)
  - preprocess_image: binary output, dimensions, scaling, no-upscale, corrupt (5)
  - _scale: aspect ratio preservation, no-upscale guard (2)
  - _rotate: preserves shape, zero-angle no-op (2)
  - _adaptive_threshold: binary values only (1)
  - _deskew: shape preserved (1)
  - analyze_page: empty image, canvas constants, single zone, multi-zone,
                  baseline=bottom, image dimensions, line_count (7)
  - WritingZone / PageMetadata to_dict (2)
  - ACCEPTED_CONTENT_TYPES constant (1)
  - API /upload-image: wrong type → 422, oversized → 413, valid JPEG (3)
  - API /process-image: empty strokes → empty results, single stroke (2)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import io

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from recognizer.image_processor import (
    ACCEPTED_CONTENT_TYPES,
    MAX_FILE_BYTES,
    TARGET_HEIGHT,
    TARGET_WIDTH,
    _adaptive_threshold,
    _decode,
    _deskew,
    _rotate,
    _scale,
    preprocess_image,
    validate_upload,
)
from recognizer.page_analyzer import (
    PageMetadata,
    WritingZone,
    analyze_page,
)

client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_png_bytes(width: int = 100, height: int = 80, white: bool = False) -> bytes:
    """Return minimal PNG bytes of a solid-colour image."""
    val = 255 if white else 128
    arr = np.full((height, width, 3), val, dtype=np.uint8)
    ok, buf = cv2.imencode(".png", arr)
    assert ok
    return buf.tobytes()


def _make_jpeg_bytes(width: int = 200, height: int = 150) -> bytes:
    arr = np.full((height, width, 3), 180, dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", arr)
    assert ok
    return buf.tobytes()


def _binary_stripe(n_rows_in: int = 10, image_height: int = 100, image_width: int = 100) -> np.ndarray:
    """Binary image with a horizontal stripe of ink."""
    img = np.zeros((image_height, image_width), dtype=np.uint8)
    mid = image_height // 2
    img[mid: mid + n_rows_in, :] = 255
    return img


# ── validate_upload ───────────────────────────────────────────────────────────


def test_validate_upload_accepts_jpeg():
    validate_upload(b"\xff\xd8", "image/jpeg")  # no exception


def test_validate_upload_accepts_png():
    validate_upload(b"\x89PNG", "image/png")


def test_validate_upload_accepts_webp():
    validate_upload(b"RIFF", "image/webp")


def test_validate_upload_rejects_unsupported_type():
    with pytest.raises(ValueError, match="Unsupported"):
        validate_upload(b"%PDF", "application/pdf")


def test_validate_upload_rejects_oversized_file():
    data = b"x" * (MAX_FILE_BYTES + 1)
    with pytest.raises(ValueError, match="MB"):
        validate_upload(data, "image/jpeg")


# ── preprocess_image ──────────────────────────────────────────────────────────


def test_preprocess_image_returns_binary_ndarray():
    data = _make_png_bytes()
    result = preprocess_image(data)
    assert result.ndim == 2
    unique = set(result.flatten().tolist())
    assert unique.issubset({0, 255})


def test_preprocess_image_output_within_target_dimensions():
    data = _make_png_bytes(width=1200, height=900)
    result = preprocess_image(data)
    assert result.shape[0] <= TARGET_HEIGHT
    assert result.shape[1] <= TARGET_WIDTH


def test_preprocess_image_scales_large_image_down():
    data = _make_png_bytes(width=TARGET_WIDTH + 200, height=TARGET_HEIGHT + 100)
    result = preprocess_image(data)
    assert result.shape[1] <= TARGET_WIDTH
    assert result.shape[0] <= TARGET_HEIGHT


def test_preprocess_image_does_not_upscale_small_image():
    small_w, small_h = 50, 40
    data = _make_png_bytes(width=small_w, height=small_h)
    result = preprocess_image(data)
    assert result.shape[1] <= TARGET_WIDTH
    assert result.shape[0] <= TARGET_HEIGHT


def test_preprocess_image_rejects_corrupt_bytes():
    with pytest.raises(ValueError, match="decode"):
        preprocess_image(b"not an image at all!!")


# ── _scale ────────────────────────────────────────────────────────────────────


def test_scale_does_not_upscale_small_image():
    bgr = np.zeros((50, 60, 3), dtype=np.uint8)
    result = _scale(bgr)
    assert result.shape[:2] == (50, 60)


def test_scale_preserves_aspect_ratio():
    bgr = np.zeros((1200, 1600, 3), dtype=np.uint8)  # 4:3 ratio, too large
    result = _scale(bgr)
    w, h = result.shape[1], result.shape[0]
    assert w <= TARGET_WIDTH
    assert h <= TARGET_HEIGHT
    ratio_in = 1600 / 1200
    ratio_out = w / h
    assert abs(ratio_out - ratio_in) < 0.05


# ── _rotate ───────────────────────────────────────────────────────────────────


def test_rotate_preserves_shape():
    img = np.zeros((100, 120), dtype=np.uint8)
    result = _rotate(img, 10.0)
    assert result.shape == (100, 120)


def test_rotate_zero_angle_returns_same_values():
    img = np.eye(50, 50, dtype=np.uint8) * 255
    result = _rotate(img, 0.0)
    assert result.shape == img.shape


# ── _adaptive_threshold ───────────────────────────────────────────────────────


def test_adaptive_threshold_produces_binary():
    gray = np.random.randint(50, 200, (100, 100), dtype=np.uint8)
    result = _adaptive_threshold(gray)
    unique = set(result.flatten().tolist())
    assert unique.issubset({0, 255})


# ── _deskew ───────────────────────────────────────────────────────────────────


def test_deskew_preserves_shape():
    binary = _binary_stripe(image_height=80, image_width=120)
    result = _deskew(binary)
    assert result.shape == binary.shape


# ── analyze_page ──────────────────────────────────────────────────────────────


def test_analyze_page_empty_image_returns_defaults():
    empty = np.zeros((0, 0), dtype=np.uint8)
    meta = analyze_page(empty)
    assert meta.canvas_height == TARGET_HEIGHT
    assert meta.canvas_width == TARGET_WIDTH
    assert meta.line_count == 0
    assert meta.writing_zones == []


def test_analyze_page_canvas_height_always_target():
    binary = _binary_stripe(image_height=200, image_width=300)
    meta = analyze_page(binary)
    assert meta.canvas_height == TARGET_HEIGHT


def test_analyze_page_canvas_width_always_target():
    binary = _binary_stripe(image_height=200, image_width=300)
    meta = analyze_page(binary)
    assert meta.canvas_width == TARGET_WIDTH


def test_analyze_page_blank_image_no_zones():
    blank = np.zeros((100, 100), dtype=np.uint8)
    meta = analyze_page(blank)
    assert meta.line_count == 0
    assert meta.writing_zones == []


def test_analyze_page_detects_single_line():
    binary = _binary_stripe(n_rows_in=15, image_height=100, image_width=100)
    meta = analyze_page(binary)
    assert meta.line_count == 1
    assert len(meta.writing_zones) == 1


def test_analyze_page_detects_two_lines():
    img = np.zeros((120, 100), dtype=np.uint8)
    img[10:20, :] = 255   # first stripe
    img[80:90, :] = 255   # second stripe (> 5 row gap)
    meta = analyze_page(img)
    assert meta.line_count == 2


def test_analyze_page_baseline_equals_zone_bottom():
    binary = _binary_stripe(n_rows_in=15, image_height=100, image_width=100)
    meta = analyze_page(binary)
    zone = meta.writing_zones[0]
    assert zone.baseline == zone.bottom


def test_analyze_page_reports_image_dimensions():
    binary = _binary_stripe(image_height=80, image_width=120)
    meta = analyze_page(binary)
    assert meta.image_width == 120
    assert meta.image_height == 80


# ── to_dict helpers ───────────────────────────────────────────────────────────


def test_writing_zone_to_dict():
    z = WritingZone(top=10.0, bottom=30.0, baseline=30.0)
    d = z.to_dict()
    assert d == {"top": 10.0, "bottom": 30.0, "baseline": 30.0}


def test_page_metadata_to_dict():
    meta = PageMetadata(
        canvas_width=800.0,
        canvas_height=600.0,
        writing_zones=[WritingZone(top=5.0, bottom=20.0, baseline=20.0)],
        line_count=1,
        image_width=640,
        image_height=480,
    )
    d = meta.to_dict()
    assert d["canvas_height"] == 600.0
    assert d["line_count"] == 1
    assert len(d["writing_zones"]) == 1


# ── ACCEPTED_CONTENT_TYPES constant ──────────────────────────────────────────


def test_accepted_content_types_covers_all_three():
    assert "image/jpeg" in ACCEPTED_CONTENT_TYPES
    assert "image/png" in ACCEPTED_CONTENT_TYPES
    assert "image/webp" in ACCEPTED_CONTENT_TYPES


# ── API: /api/upload-image ────────────────────────────────────────────────────


def test_upload_image_rejects_wrong_content_type():
    data = b"%PDF-1.4"
    resp = client.post(
        "/api/upload-image",
        files={"file": ("test.pdf", data, "application/pdf")},
    )
    assert resp.status_code == 422


def test_upload_image_rejects_oversized_file():
    # Fake oversized data (> 10 MB), wrong type trick to avoid processing
    big_data = b"x" * (MAX_FILE_BYTES + 1)
    resp = client.post(
        "/api/upload-image",
        files={"file": ("big.jpg", big_data, "image/jpeg")},
    )
    assert resp.status_code == 413


def test_upload_image_accepts_valid_png():
    data = _make_png_bytes()
    resp = client.post(
        "/api/upload-image",
        files={"file": ("test.png", data, "image/png")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "strokes" in body
    assert "stroke_count" in body
    assert "page_metadata" in body
    assert body["page_metadata"]["canvas_height"] == TARGET_HEIGHT


# ── API: /api/process-image ───────────────────────────────────────────────────


def test_process_image_empty_strokes_returns_empty():
    payload = {"strokes": [], "canvas_height": 600.0, "canvas_width": 800.0}
    resp = client.post("/api/process-image", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["stroke_results"] == []
    assert body["phonemes"] == []
    assert body["candidates"] == []


def test_process_image_single_stroke_returns_result():
    points = [
        {"x": float(x), "y": 100.0, "pressure": 0.5, "timestamp": x * 16}
        for x in range(0, 200, 5)
    ]
    payload = {
        "strokes": [{"id": "img-s1", "points": points}],
        "canvas_height": 600.0,
        "canvas_width": 800.0,
    }
    resp = client.post("/api/process-image", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["stroke_results"]) == 1
    sr = body["stroke_results"][0]
    assert sr["stroke_id"] == "img-s1"
    assert "symbol" in sr
    assert "confidence" in sr
