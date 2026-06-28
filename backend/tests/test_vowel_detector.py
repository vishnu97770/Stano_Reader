"""
Unit tests for M15.5 — Vowel Sign Recognition.

Coverage (30 tests):
  - All 12 VowelDefinition entries: symbol, IPA, degree, position, mark (12)
  - Mark classification: dot, dash, and too-large stroke (3)
  - Degree detection: near start → 1, near middle → 2, near end → 3 (3)
  - Before/after position detection (2)
  - Nearest-consonant selection (2)
  - No nearby strokes → not attached (1)
  - Full vowel detection: is_vowel=True for small marks (2)
  - Full vowel detection: is_vowel=False for large strokes (1)
  - Phoneme mapper with vowel_inserts (4)
  - boost_by_vowels: boost applied / not applied (4)
  - VowelResult schema fields (1)
  - API endpoint: 422 on empty points (1)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi import HTTPException

from app.api.vowel import detect_vowel_endpoint
from app.schemas.vowel import DetectVowelRequest, NearbyStrokeInfo, StrokePointSchema
from recognizer.candidate_engine import CandidateResult, boost_by_vowels
from recognizer.phoneme_mapper import map_symbols_to_phonemes
from recognizer.schemas import VowelResult
from recognizer.vowel_definitions import (
    VOWEL_BY_KEY,
    VOWEL_BY_SYMBOL,
    VOWEL_DEFINITIONS,
    DOT_MAX_PX,
    DASH_MAX_PX,
    PROXIMITY_PX,
)
from recognizer.vowel_detector import detect_vowel
from recognizer.vowel_rules import (
    NearbyConsonant,
    Point,
    classify_mark,
    detect_degree,
    detect_position,
    find_nearest_consonant,
    resolve_vowel,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dot_points(cx: float = 100.0, cy: float = 100.0) -> list[Point]:
    """A single-point dot at (cx, cy)."""
    return [Point(cx, cy)]


def _dash_points(
    x0: float = 100.0,
    y0: float = 100.0,
    length: float = 18.0,
    horizontal: bool = True,
) -> list[Point]:
    """A short horizontal or vertical dash."""
    if horizontal:
        return [Point(x0, y0), Point(x0 + length, y0)]
    return [Point(x0, y0), Point(x0, y0 + length)]


def _long_stroke_points(x0: float = 0.0, y0: float = 0.0, length: float = 120.0) -> list[Point]:
    """A normal-length consonant stroke (too long to be a vowel mark)."""
    return [Point(x0, y0 + i * (length / 10)) for i in range(11)]


def _nearby(
    stroke_id: str = "cons-1",
    family: str = "TD_FAMILY",
    cx: float = 150.0,
    cy: float = 100.0,
    sx: float = 150.0,
    sy: float = 50.0,
    ex: float = 150.0,
    ey: float = 150.0,
) -> NearbyConsonant:
    return NearbyConsonant(
        stroke_id=stroke_id,
        family=family,
        centroid=Point(cx, cy),
        start=Point(sx, sy),
        end=Point(ex, ey),
    )


# ── 1. All 12 VowelDefinitions are present and correctly typed ────────────────

@pytest.mark.parametrize("symbol,ipa,degree,position,mark", [
    ("DOT1_BEFORE",  "/æ/",  1, "before", "dot"),
    ("DOT1_AFTER",   "/eɪ/", 1, "after",  "dot"),
    ("DASH1_BEFORE", "/ɑː/", 1, "before", "dash"),
    ("DASH1_AFTER",  "/ɛ/",  1, "after",  "dash"),
    ("DOT2_BEFORE",  "/ɪ/",  2, "before", "dot"),
    ("DOT2_AFTER",   "/iː/", 2, "after",  "dot"),
    ("DASH2_BEFORE", "/ʌ/",  2, "before", "dash"),
    ("DASH2_AFTER",  "/ɜː/", 2, "after",  "dash"),
    ("DOT3_BEFORE",  "/ɒ/",  3, "before", "dot"),
    ("DOT3_AFTER",   "/oʊ/", 3, "after",  "dot"),
    ("DASH3_BEFORE", "/ʊ/",  3, "before", "dash"),
    ("DASH3_AFTER",  "/uː/", 3, "after",  "dash"),
])
def test_vowel_definition_exists(symbol, ipa, degree, position, mark):
    defn = VOWEL_BY_SYMBOL[symbol]
    assert defn.ipa == ipa
    assert defn.degree == degree
    assert defn.position == position
    assert defn.mark == mark


def test_vowel_definitions_count():
    assert len(VOWEL_DEFINITIONS) == 12


def test_vowel_by_key_complete():
    """Every combination of (degree, position, mark) maps to a unique definition."""
    keys = {(v.degree, v.position, v.mark) for v in VOWEL_DEFINITIONS}
    assert len(keys) == 12


# ── 2. Mark classification ─────────────────────────────────────────────────────

def test_classify_mark_dot():
    pts = _dot_points(100, 100)
    assert classify_mark(pts) == "dot"


def test_classify_mark_dash_horizontal():
    pts = _dash_points(length=18.0, horizontal=True)
    assert classify_mark(pts) == "dash"


def test_classify_mark_dash_vertical():
    pts = _dash_points(length=18.0, horizontal=False)
    assert classify_mark(pts) == "dash"


def test_classify_mark_too_large_returns_none():
    pts = _long_stroke_points()
    assert classify_mark(pts) is None


def test_classify_mark_empty_returns_none():
    assert classify_mark([]) is None


# ── 3. Degree detection ───────────────────────────────────────────────────────

def test_detect_degree_near_start():
    cons_start = Point(150, 50)
    cons_end = Point(150, 150)
    vowel = Point(100, 60)   # 10/100 = 10% along → degree 1
    assert detect_degree(vowel, cons_start, cons_end) == 1


def test_detect_degree_near_middle():
    cons_start = Point(150, 50)
    cons_end = Point(150, 150)
    vowel = Point(100, 100)  # 50/100 = 50% along → degree 2
    assert detect_degree(vowel, cons_start, cons_end) == 2


def test_detect_degree_near_end():
    cons_start = Point(150, 50)
    cons_end = Point(150, 150)
    vowel = Point(100, 140)  # 90/100 = 90% along → degree 3
    assert detect_degree(vowel, cons_start, cons_end) == 3


def test_detect_degree_degenerate_stroke():
    p = Point(100, 100)
    assert detect_degree(Point(90, 100), p, p) == 2


# ── 4. Position detection (before / after) ────────────────────────────────────

def test_detect_position_before_vertical_stroke():
    # Downward stroke; vowel to the left → before
    start = Point(150, 50)
    end = Point(150, 150)
    centroid = Point(150, 100)
    vowel = Point(90, 100)   # left of stroke
    assert detect_position(vowel, start, end, centroid) == "before"


def test_detect_position_after_vertical_stroke():
    start = Point(150, 50)
    end = Point(150, 150)
    centroid = Point(150, 100)
    vowel = Point(210, 100)  # right of stroke
    assert detect_position(vowel, start, end, centroid) == "after"


# ── 5. Nearest-consonant selection ────────────────────────────────────────────

def test_find_nearest_consonant_returns_closest():
    vowel_pos = Point(100, 100)
    near = _nearby("near", cx=110, cy=100)
    far = _nearby("far", cx=200, cy=100)
    result = find_nearest_consonant(vowel_pos, [near, far])
    assert result is not None
    assert result.stroke_id == "near"


def test_find_nearest_consonant_out_of_range_returns_none():
    vowel_pos = Point(0, 0)
    distant = _nearby("far", cx=500, cy=500)
    assert find_nearest_consonant(vowel_pos, [distant]) is None


def test_find_nearest_consonant_empty_returns_none():
    assert find_nearest_consonant(Point(100, 100), []) is None


# ── 6. No nearby strokes → not vowel ─────────────────────────────────────────

def test_resolve_vowel_no_nearby_returns_none():
    pts = _dot_points(100, 100)
    defn, nearest, conf, reason = resolve_vowel(pts, [])
    assert defn is None
    assert nearest is None
    assert conf == 0.0
    assert "No nearby" in reason


# ── 7. Full detect_vowel integration ─────────────────────────────────────────

def _raw_points(*pts: tuple[float, float]) -> list[dict]:
    return [{"x": x, "y": y} for x, y in pts]


def _raw_nearby(stroke_id="cons-1", family="TD_FAMILY",
                cx=150.0, cy=100.0, sx=150.0, sy=50.0, ex=150.0, ey=150.0):
    return {
        "stroke_id": stroke_id, "family": family,
        "centroid_x": cx, "centroid_y": cy,
        "start_x": sx, "start_y": sy,
        "end_x": ex, "end_y": ey,
    }


def test_detect_vowel_dot_before_degree2():
    # Dot at x=90, y=100 beside a downward consonant at x=150 y=50..150
    pts = _raw_points((90, 100))
    nearby = [_raw_nearby()]
    result = detect_vowel("v1", pts, nearby)
    assert result.is_vowel is True
    assert result.detected is True
    assert result.degree == 2
    assert result.position == "before"
    assert result.vowel_symbol == "DOT2_BEFORE"
    assert result.ipa == "/ɪ/"
    assert result.attached_to_stroke_id == "cons-1"
    assert result.confidence > 0.0
    assert result.reasoning != ""


def test_detect_vowel_dot_after_degree2():
    pts = _raw_points((210, 100))
    nearby = [_raw_nearby()]
    result = detect_vowel("v2", pts, nearby)
    assert result.is_vowel is True
    assert result.vowel_symbol == "DOT2_AFTER"
    assert result.ipa == "/iː/"


def test_detect_vowel_long_stroke_not_vowel():
    pts = _raw_points(*[(0, i * 12) for i in range(11)])
    nearby = [_raw_nearby()]
    result = detect_vowel("c1", pts, nearby)
    assert result.is_vowel is False
    assert result.detected is False
    assert result.vowel_symbol is None
    assert result.ipa is None
    assert result.attached_to_stroke_id is None
    assert result.confidence == 0.0


def test_detect_vowel_echoes_stroke_id():
    pts = _raw_points((90, 100))
    nearby = [_raw_nearby()]
    result = detect_vowel("unique-id-abc", pts, nearby)
    assert result.stroke_id == "unique-id-abc"


def test_detect_vowel_no_nearby_is_vowel_false():
    pts = _raw_points((90, 100))
    result = detect_vowel("v3", pts, [])
    assert result.is_vowel is False
    assert result.reasoning != ""


# ── 8. Phoneme mapper with vowel_inserts ──────────────────────────────────────

def test_phoneme_mapper_no_inserts_unchanged():
    assert map_symbols_to_phonemes(["P", "T"]) == ["/p/", "/t/"]


def test_phoneme_mapper_insert_before_first():
    result = map_symbols_to_phonemes(["P"], [{"after_index": -1, "ipa": "/ɪ/"}])
    assert result == ["/ɪ/", "/p/"]


def test_phoneme_mapper_insert_after_first():
    result = map_symbols_to_phonemes(["P", "T"], [{"after_index": 0, "ipa": "/ɪ/"}])
    assert result == ["/p/", "/ɪ/", "/t/"]


def test_phoneme_mapper_multiple_inserts():
    result = map_symbols_to_phonemes(
        ["P", "T"],
        [{"after_index": -1, "ipa": "/ɪ/"}, {"after_index": 0, "ipa": "/æ/"}],
    )
    assert result == ["/ɪ/", "/p/", "/æ/", "/t/"]


def test_phoneme_mapper_empty_inserts_list():
    assert map_symbols_to_phonemes(["P"], []) == ["/p/"]


def test_phoneme_mapper_none_inserts():
    assert map_symbols_to_phonemes(["P"], None) == ["/p/"]


# ── 9. Candidate boost by vowels ──────────────────────────────────────────────

def test_boost_by_vowels_boosts_matching_word():
    candidates = [CandidateResult(word="bit", confidence=0.5)]
    boosted = boost_by_vowels(candidates, [{"ipa": "/ɪ/"}])
    assert boosted[0].confidence > 0.5


def test_boost_by_vowels_no_match_unchanged():
    candidates = [CandidateResult(word="moon", confidence=0.5)]
    boosted = boost_by_vowels(candidates, [{"ipa": "/ɪ/"}])
    # "moon" contains 'oo' which maps to /uː/ not /ɪ/; no 'i' either
    assert boosted[0].confidence == 0.5


def test_boost_by_vowels_empty_signals():
    candidates = [CandidateResult(word="bit", confidence=0.5)]
    assert boost_by_vowels(candidates, []) == candidates


def test_boost_by_vowels_confidence_capped_at_one():
    candidates = [CandidateResult(word="bit", confidence=0.98)]
    boosted = boost_by_vowels(candidates, [{"ipa": "/ɪ/"}])
    assert boosted[0].confidence <= 1.0


def test_boost_by_vowels_preserves_sort_order():
    candidates = [
        CandidateResult(word="bit", confidence=0.5),
        CandidateResult(word="moon", confidence=0.9),
    ]
    boosted = boost_by_vowels(candidates, [{"ipa": "/ɪ/"}])
    assert boosted[0].word == "moon"  # still highest after boost


# ── 10. VowelResult schema completeness ───────────────────────────────────────

def test_vowel_result_schema_all_fields():
    r = VowelResult(
        stroke_id="x",
        is_vowel=True,
        vowel_symbol="DOT2_BEFORE",
        ipa="/ɪ/",
        degree=2,
        position="before",
        attached_to_stroke_id="cons-1",
        detected=True,
        confidence=0.8,
        reasoning="test",
        alternatives=[],
    )
    assert r.stroke_id == "x"
    assert r.is_vowel is True
    assert r.vowel_symbol == "DOT2_BEFORE"
    assert r.ipa == "/ɪ/"
    assert r.degree == 2
    assert r.position == "before"
    assert r.attached_to_stroke_id == "cons-1"
    assert r.detected is True
    assert r.confidence == 0.8
    assert r.reasoning == "test"
    assert r.alternatives == []


# ── 11. API endpoint guard ─────────────────────────────────────────────────────

def test_api_endpoint_rejects_empty_points():
    body = DetectVowelRequest(stroke_id="x", points=[], nearby_strokes=[])
    with pytest.raises(HTTPException) as exc_info:
        detect_vowel_endpoint(body)
    assert exc_info.value.status_code == 422


def test_api_endpoint_returns_vowel_result():
    body = DetectVowelRequest(
        stroke_id="test-id",
        points=[StrokePointSchema(x=90, y=100)],
        nearby_strokes=[
            NearbyStrokeInfo(
                stroke_id="cons-1",
                family="TD_FAMILY",
                centroid_x=150, centroid_y=100,
                start_x=150, start_y=50,
                end_x=150, end_y=150,
            )
        ],
    )
    result = detect_vowel_endpoint(body)
    assert isinstance(result, VowelResult)
    assert result.stroke_id == "test-id"
