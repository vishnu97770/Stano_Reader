"""
Tests for M19 — Complete Consonant Coverage

Coverage (≥30 tests):
  Family definitions (5):
    - Each new family exists in FAMILY_DEFINITIONS with correct geometry
  Family classification (11):
    - Synthetic strokes route to the correct new family
    - Existing families are unaffected by the additions
  Symbol discrimination (8):
    - M vs W (length-based)
    - L vs R (curvature-based)
    - N (frequency-default in NN_FAMILY)
    - H and Y (single-member families)
    - NG appears in NN_FAMILY alternatives
  IPA mappings (9):
    - M→/m/, W→/w/, L→/l/, R→/r/, N→/n/, NG→/ŋ/, NK→/ŋk/, Y→/j/, H→/h/
  Candidate pipeline (12):
    - Direct phoneme queries return target words
    - "note", "love", "make", "run", "will", "have", "yes" all reachable
    - NG and NK words reachable
    - Full stroke-to-candidate pipeline for M, N, L, H, Y families
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from recognizer.analyzer import analyze_stroke
from recognizer.candidate_engine import get_candidates
from recognizer.family_classifier import classify_stroke
from recognizer.family_definitions import CONFIDENCE_THRESHOLD, FAMILY_DEFINITIONS
from recognizer.phoneme_definitions import PITMAN_TO_IPA
from recognizer.symbol_classifier import classify_symbol
from recognizer.symbol_definitions import FAMILY_SYMBOLS, SYMBOL_DEFINITIONS
from recognizer.symbol_rules import compute_symbol_scores


# ---------------------------------------------------------------------------
# Synthetic stroke generators
# ---------------------------------------------------------------------------

def _straight(angle_deg: float, length: float = 80.0, n: int = 10) -> list[dict]:
    """Straight stroke whose start-to-end bearing equals angle_deg."""
    rad = math.radians(angle_deg)
    dx = math.cos(rad) * length / (n - 1)
    dy = math.sin(rad) * length / (n - 1)
    return [
        {"x": round(i * dx, 2), "y": round(i * dy, 2),
         "pressure": 0.5, "timestamp": i * 50}
        for i in range(n)
    ]


def _curved(chord_angle_deg: float, length: float = 80.0,
            bow: float = 0.25, n: int = 16) -> list[dict]:
    """
    Open curve: chord goes in chord_angle_deg direction, arc bows
    perpendicularly.  bow=0.25 means the midpoint deviates 25% of length.
    """
    rad = math.radians(chord_angle_deg)
    perp = rad + math.pi / 2
    end_x = math.cos(rad) * length
    end_y = math.sin(rad) * length
    pts = []
    for i in range(n):
        t = i / (n - 1)
        offset = math.sin(t * math.pi) * bow * length
        pts.append({
            "x": round(t * end_x + offset * math.cos(perp), 2),
            "y": round(t * end_y + offset * math.sin(perp), 2),
            "pressure": 0.5,
            "timestamp": i * 50,
        })
    return pts


def _circle(n: int = 20, radius: float = 30.0) -> list[dict]:
    """Closed loop — high curvature_ratio for SZ_FAMILY testing."""
    return [
        {"x": round(radius * math.cos(2 * math.pi * i / n), 2),
         "y": round(radius * math.sin(2 * math.pi * i / n), 2),
         "pressure": 0.5, "timestamp": i * 50}
        for i in range(n + 1)  # +1 closes the loop back to start
    ]


def _classify_family(points: list[dict]) -> str:
    features = analyze_stroke("test", points)
    return classify_stroke(features).family


def _classify_symbol_name(points: list[dict]) -> str:
    features = analyze_stroke("test", points)
    fr = classify_stroke(features)
    sr = classify_symbol(features, fr)
    return sr.symbol


# ---------------------------------------------------------------------------
# 1. Family definitions — existence and geometry
# ---------------------------------------------------------------------------

def test_mw_family_exists():
    assert "MW_FAMILY" in FAMILY_DEFINITIONS
    defn = FAMILY_DEFINITIONS["MW_FAMILY"]
    assert defn.expect_curve is True
    assert abs(defn.angle_center - 0.0) < 1.0
    assert "M" in defn.members and "W" in defn.members


def test_lr_family_exists():
    assert "LR_FAMILY" in FAMILY_DEFINITIONS
    defn = FAMILY_DEFINITIONS["LR_FAMILY"]
    assert abs(defn.angle_center - 325.0) < 1.0
    assert "L" in defn.members and "R" in defn.members


def test_nn_family_exists():
    assert "NN_FAMILY" in FAMILY_DEFINITIONS
    defn = FAMILY_DEFINITIONS["NN_FAMILY"]
    assert defn.expect_curve is True
    assert abs(defn.angle_center - 90.0) < 1.0
    assert "N" in defn.members and "NG" in defn.members and "NK" in defn.members


def test_y_family_exists():
    assert "Y_FAMILY" in FAMILY_DEFINITIONS
    defn = FAMILY_DEFINITIONS["Y_FAMILY"]
    assert defn.expect_curve is True
    assert "Y" in defn.members


def test_h_family_exists():
    assert "H_FAMILY" in FAMILY_DEFINITIONS
    defn = FAMILY_DEFINITIONS["H_FAMILY"]
    assert defn.expect_curve is False
    assert "H" in defn.members


# ---------------------------------------------------------------------------
# 2. Family classification from synthetic strokes
# ---------------------------------------------------------------------------

def test_curved_rightward_stroke_is_mw_family():
    pts = _curved(chord_angle_deg=0, length=90)
    assert _classify_family(pts) == "MW_FAMILY"


def test_curved_downward_stroke_is_nn_family():
    pts = _curved(chord_angle_deg=90, length=80)
    assert _classify_family(pts) == "NN_FAMILY"


def test_straight_up_right_stroke_is_lr_family():
    pts = _straight(angle_deg=325, length=80)
    assert _classify_family(pts) == "LR_FAMILY"


def test_curved_up_right_stroke_is_lr_family():
    """R is a curved up-right stroke — LR_FAMILY handles both curvatures."""
    pts = _curved(chord_angle_deg=325, length=70)
    assert _classify_family(pts) == "LR_FAMILY"


def test_curved_down_left_stroke_is_y_family():
    pts = _curved(chord_angle_deg=200, length=60)
    assert _classify_family(pts) == "Y_FAMILY"


def test_straight_up_left_stroke_is_h_family():
    pts = _straight(angle_deg=250, length=50)
    assert _classify_family(pts) == "H_FAMILY"


def test_straight_downstroke_still_pb_family():
    """PB_FAMILY must be unaffected by NN_FAMILY addition at same angle."""
    pts = _straight(angle_deg=90, length=80)
    assert _classify_family(pts) == "PB_FAMILY"


def test_straight_horizontal_still_thdh_family():
    """THDH_FAMILY must be unaffected by MW_FAMILY addition at same angle."""
    pts = _straight(angle_deg=0, length=80)
    assert _classify_family(pts) == "THDH_FAMILY"


def test_upstroke_still_shzh_family():
    """SHZH_FAMILY must be unaffected by LR_FAMILY addition nearby."""
    pts = _straight(angle_deg=290, length=80)
    assert _classify_family(pts) == "SHZH_FAMILY"


def test_highly_circular_stroke_is_sz_not_nn():
    """Strokes with curvature_ratio > 2.5 must go to SZ_FAMILY, not NN_FAMILY."""
    pts = _circle(n=24, radius=30)
    family = _classify_family(pts)
    assert family == "SZ_FAMILY", f"Expected SZ_FAMILY, got {family}"


def test_new_families_confidence_above_threshold():
    """All new families must score above CONFIDENCE_THRESHOLD on canonical strokes."""
    cases = [
        ("MW_FAMILY", _curved(0, 90)),
        ("LR_FAMILY", _straight(325, 80)),
        ("NN_FAMILY", _curved(90, 80)),
        ("Y_FAMILY",  _curved(200, 60)),
        ("H_FAMILY",  _straight(250, 50)),
    ]
    for expected_family, pts in cases:
        features = analyze_stroke("test", pts)
        result = classify_stroke(features)
        assert result.family == expected_family, (
            f"Expected {expected_family}, got {result.family}"
        )
        assert result.confidence >= CONFIDENCE_THRESHOLD, (
            f"{expected_family} confidence {result.confidence:.3f} below threshold"
        )


# ---------------------------------------------------------------------------
# 3. Symbol discrimination within new families
# ---------------------------------------------------------------------------

def test_long_curved_rightward_is_m():
    """Stroke length ≥ 70 px → M."""
    pts = _curved(0, length=90)
    assert _classify_symbol_name(pts) == "M"


def test_short_curved_rightward_is_w():
    """Stroke length ≤ 35 px → W."""
    pts = _curved(0, length=25)
    assert _classify_symbol_name(pts) == "W"


def test_straight_up_right_is_l():
    """Straight LR stroke → L."""
    pts = _straight(325, length=80)
    assert _classify_symbol_name(pts) == "L"


def test_curved_up_right_is_r():
    """Curved LR stroke → R."""
    pts = _curved(325, length=70)
    assert _classify_symbol_name(pts) == "R"


def test_nn_family_default_symbol_is_n():
    """Without length/pressure data to distinguish, N is the most frequent."""
    pts = _curved(90, length=80)
    assert _classify_symbol_name(pts) == "N"


def test_nn_family_ng_in_alternatives():
    """NG must appear in the symbol alternatives for an NN_FAMILY stroke."""
    pts = _curved(90, length=80)
    features = analyze_stroke("test", pts)
    fr = classify_stroke(features)
    sr = classify_symbol(features, fr)
    alt_symbols = [a.symbol for a in sr.alternatives]
    assert "NG" in alt_symbols, f"NG not in alternatives: {alt_symbols}"


def test_h_family_symbol_is_h():
    pts = _straight(250, length=50)
    assert _classify_symbol_name(pts) == "H"


def test_y_family_symbol_is_y():
    pts = _curved(200, length=60)
    assert _classify_symbol_name(pts) == "Y"


# ---------------------------------------------------------------------------
# 4. IPA mappings for all nine new symbols
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("symbol,expected_ipa", [
    ("M",  "/m/"),
    ("W",  "/w/"),
    ("L",  "/l/"),
    ("R",  "/r/"),
    ("N",  "/n/"),
    ("NG", "/ŋ/"),
    ("NK", "/ŋk/"),
    ("Y",  "/j/"),
    ("H",  "/h/"),
])
def test_ipa_mapping(symbol, expected_ipa):
    assert PITMAN_TO_IPA.get(symbol) == expected_ipa, (
        f"Expected {symbol} → {expected_ipa}, got {PITMAN_TO_IPA.get(symbol)}"
    )


# ---------------------------------------------------------------------------
# 5. Candidate pipeline — target words reachable
# ---------------------------------------------------------------------------

def _words(phonemes: list[str], limit: int = 20) -> list[str]:
    return [c.word for c in get_candidates(phonemes, max_results=limit)]


def test_note_reachable_via_n_t():
    assert "note" in _words(["/n/", "/t/"])


def test_love_reachable_via_l_v():
    assert "love" in _words(["/l/", "/v/"])


def test_make_reachable_via_m_k():
    assert "make" in _words(["/m/", "/k/"])


def test_run_reachable_via_r_n():
    assert "run" in _words(["/r/", "/n/"])


def test_will_reachable_via_w_l():
    assert "will" in _words(["/w/", "/l/"])


def test_have_reachable_via_h_v():
    assert "have" in _words(["/h/", "/v/"])


def test_yes_reachable_via_y_s():
    assert "yes" in _words(["/j/", "/s/"])


def test_ring_reachable_via_r_ng():
    """NG (velar nasal) words are reachable."""
    assert "ring" in _words(["/r/", "/ŋ/"])


def test_bank_reachable_via_b_nk():
    """NK (nasal-velar cluster) words are reachable."""
    assert "bank" in _words(["/b/", "/ŋk/"])


def test_full_pipeline_m_produces_make():
    """Full stroke → family → symbol → IPA → candidates for M+K."""
    m_pts = _curved(0, length=90)   # long curve → MW_FAMILY → M → /m/
    k_pts = _straight(20, length=80)  # near-horizontal right → KG_FAMILY → K → /k/

    phonemes = []
    for pts in [m_pts, k_pts]:
        features = analyze_stroke("test", pts)
        fr = classify_stroke(features)
        sr = classify_symbol(features, fr)
        ipa = PITMAN_TO_IPA.get(sr.symbol, "")
        if ipa:
            phonemes.append(ipa)

    assert phonemes == ["/m/", "/k/"], f"Unexpected phoneme sequence: {phonemes}"
    assert "make" in _words(phonemes)


def test_full_pipeline_n_produces_note():
    """Full stroke → family → symbol → IPA → candidates for N+T."""
    n_pts = _curved(90, length=80)    # curved down → NN_FAMILY → N → /n/
    t_pts = _straight(50, length=80)  # 45° down-right → TD_FAMILY → T → /t/

    phonemes = []
    for pts in [n_pts, t_pts]:
        features = analyze_stroke("test", pts)
        fr = classify_stroke(features)
        sr = classify_symbol(features, fr)
        ipa = PITMAN_TO_IPA.get(sr.symbol, "")
        if ipa:
            phonemes.append(ipa)

    assert phonemes == ["/n/", "/t/"], f"Unexpected phoneme sequence: {phonemes}"
    assert "note" in _words(phonemes)


def test_full_pipeline_h_produces_have():
    """Full stroke → family → symbol → IPA → candidates for H+V."""
    h_pts = _straight(250, length=50)  # up-left → H_FAMILY → H → /h/

    features = analyze_stroke("test", h_pts)
    fr = classify_stroke(features)
    sr = classify_symbol(features, fr)
    assert sr.symbol == "H"
    assert PITMAN_TO_IPA["H"] == "/h/"

    # Verify "have" is reachable when /h/ + /v/ are queried
    assert "have" in _words(["/h/", "/v/"])


def test_full_pipeline_y_produces_yes():
    """Full stroke → family → symbol → IPA → candidates for Y+S."""
    y_pts = _curved(200, length=60)   # curved down-left → Y_FAMILY → Y → /j/

    features = analyze_stroke("test", y_pts)
    fr = classify_stroke(features)
    sr = classify_symbol(features, fr)
    assert sr.symbol == "Y"
    assert PITMAN_TO_IPA["Y"] == "/j/"

    # Verify "yes" is reachable when /j/ + /s/ are queried
    assert "yes" in _words(["/j/", "/s/"])
