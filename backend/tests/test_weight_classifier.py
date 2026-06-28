"""
Unit tests for M14 Task 4 additions to weight_classifier.py:
  - detected=False when no pressure data is present
  - detected=True for real AMBIGUOUS classification (pressure data available)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from recognizer.weight_classifier import classify_weight


def _points_with_pressure(pressure: float, n: int = 5) -> list[dict]:
    return [{"x": float(i), "y": 0.0, "pressure": pressure, "timestamp": i} for i in range(n)]


def _points_without_pressure(n: int = 5) -> list[dict]:
    return [{"x": float(i), "y": 0.0, "timestamp": i} for i in range(n)]


# ── detected field — no-data path ────────────────────────────────────────────

def test_detected_false_when_no_pressure_data():
    """No pressure key in any point → detected must be False."""
    result = classify_weight("w-nodata", _points_without_pressure())
    assert result.detected is False


def test_weight_ambiguous_and_confidence_zero_when_no_pressure_data():
    """No-data path must also produce weight=AMBIGUOUS and confidence=0.0."""
    result = classify_weight("w-nodata2", _points_without_pressure())
    assert result.weight == "AMBIGUOUS"
    assert result.confidence == 0.0


# ── detected field — real classification paths ────────────────────────────────

def test_detected_true_for_real_ambiguous():
    """Pressure in ambiguous zone → detected must be True even though weight=AMBIGUOUS."""
    result = classify_weight("w-ambig", _points_with_pressure(0.5))
    assert result.weight == "AMBIGUOUS"
    assert result.detected is True


def test_detected_true_for_light():
    """Low pressure → LIGHT classification → detected must be True."""
    result = classify_weight("w-light", _points_with_pressure(0.1))
    assert result.weight == "LIGHT"
    assert result.detected is True


def test_detected_true_for_heavy():
    """High pressure → HEAVY classification → detected must be True."""
    result = classify_weight("w-heavy", _points_with_pressure(0.9))
    assert result.weight == "HEAVY"
    assert result.detected is True
