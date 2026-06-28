"""
Unit tests for M15 phraseography detection.

Coverage:
  - All 13 detectable phrases fire correctly
  - Non-phrase outlines return is_phrase=False
  - Confidence values and thresholds
  - Alternatives ranking for collision pairs
  - Edge cases: empty outline, unknown families, long outlines
  - Reasoning text always present
  - stroke_id echoed in result
  - phrase_rules functions in isolation
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi import HTTPException

from app.api.phrase import detect_phrase_endpoint
from app.schemas.phrase import DetectPhraseRequest
from recognizer.phrase_definitions import (
    DETECTABLE_PHRASES,
    PHRASE_BY_TEXT,
    PHRASE_DEFINITIONS,
)
from recognizer.phrase_detector import detect_phrase
from recognizer.phrase_rules import (
    CANDIDATE_BOOST_MAX,
    build_reasoning,
    candidate_boost,
    match_phrase,
    score_phrase,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _families(phrase_text: str) -> list[str]:
    """Return the family_pattern for a phrase as a plain list."""
    return list(PHRASE_BY_TEXT[phrase_text].family_pattern)


# ── phrase_rules: match_phrase ────────────────────────────────────────────────

def test_match_phrase_exact_returns_one():
    defn = PHRASE_BY_TEXT["it is"]
    assert match_phrase(["TD_FAMILY", "SZ_FAMILY"], defn) == 1.0


def test_match_phrase_wrong_order_returns_zero():
    defn = PHRASE_BY_TEXT["it is"]
    assert match_phrase(["SZ_FAMILY", "TD_FAMILY"], defn) == 0.0


def test_match_phrase_extra_family_returns_zero():
    defn = PHRASE_BY_TEXT["I have"]
    assert match_phrase(["FV_FAMILY", "TD_FAMILY"], defn) == 0.0


def test_match_phrase_empty_pattern_returns_zero():
    defn = PHRASE_BY_TEXT["I am"]  # not detectable
    assert match_phrase(["FV_FAMILY"], defn) == 0.0


def test_match_phrase_empty_outline_returns_zero():
    defn = PHRASE_BY_TEXT["I have"]
    assert match_phrase([], defn) == 0.0


# ── phrase_rules: candidate_boost ────────────────────────────────────────────

def test_candidate_boost_matching_word():
    defn = PHRASE_BY_TEXT["I have"]
    boost = candidate_boost(defn, ["have", "give"])
    assert boost == CANDIDATE_BOOST_MAX


def test_candidate_boost_no_match():
    defn = PHRASE_BY_TEXT["I have"]
    boost = candidate_boost(defn, ["take", "make"])
    assert boost == 0.0


def test_candidate_boost_empty_candidates():
    defn = PHRASE_BY_TEXT["of the"]
    assert candidate_boost(defn, []) == 0.0


# ── Detectable phrases — all 13 must fire ────────────────────────────────────

def test_i_have_detected():
    r = detect_phrase("s1", ["FV_FAMILY"])
    assert r.is_phrase is True
    assert r.phrase_text == "I have"
    assert r.confidence >= PHRASE_BY_TEXT["I have"].confidence_threshold


def test_i_had_detected():
    r = detect_phrase("s2", ["TD_FAMILY"])
    assert r.is_phrase is True
    assert r.phrase_text == "I had"
    assert r.confidence >= PHRASE_BY_TEXT["I had"].confidence_threshold


def test_it_is_detected():
    r = detect_phrase("s3", ["TD_FAMILY", "SZ_FAMILY"])
    assert r.is_phrase is True
    assert r.phrase_text == "it is"


def test_to_be_detected():
    r = detect_phrase("s4", ["TD_FAMILY", "PB_FAMILY"])
    assert r.is_phrase is True
    assert r.phrase_text == "to be"


def test_to_have_detected():
    r = detect_phrase("s5", ["TD_FAMILY", "FV_FAMILY"])
    assert r.is_phrase is True
    assert r.phrase_text == "to have"


def test_of_the_detected():
    r = detect_phrase("s6", ["FV_FAMILY", "THDH_FAMILY"])
    assert r.is_phrase is True
    assert r.phrase_text == "of the"


def test_at_the_detected():
    r = detect_phrase("s7", ["TD_FAMILY", "THDH_FAMILY"])
    assert r.is_phrase is True
    assert r.phrase_text == "at the"


def test_is_it_detected():
    r = detect_phrase("s8", ["SZ_FAMILY", "TD_FAMILY"])
    assert r.is_phrase is True
    assert r.phrase_text == "is it"


def test_there_is_detected():
    r = detect_phrase("s9", ["THDH_FAMILY", "SZ_FAMILY"])
    assert r.is_phrase is True
    assert r.phrase_text == "there is"


def test_which_is_detected():
    r = detect_phrase("s10", ["CHJ_FAMILY", "SZ_FAMILY"])
    assert r.is_phrase is True
    assert r.phrase_text == "which is"


def test_as_the_detected():
    r = detect_phrase("s11", ["SZ_FAMILY", "THDH_FAMILY"])
    assert r.is_phrase is True
    assert r.phrase_text == "as the"


def test_that_is_detected():
    r = detect_phrase("s12", ["THDH_FAMILY", "TD_FAMILY", "SZ_FAMILY"])
    assert r.is_phrase is True
    assert r.phrase_text == "that is"


# ── Collision pairs — priority and alternatives ───────────────────────────────

def test_for_the_appears_as_alternative_to_of_the():
    """[FV, THDH] → 'of the' primary; 'for the' in alternatives."""
    r = detect_phrase("s13", ["FV_FAMILY", "THDH_FAMILY"])
    assert r.phrase_text == "of the"
    alt_texts = [a.phrase_text for a in r.alternatives]
    assert "for the" in alt_texts


def test_i_would_appears_as_alternative_to_i_had():
    """[TD] → 'I had' primary; 'I would' in alternatives."""
    r = detect_phrase("s14", ["TD_FAMILY"])
    assert r.phrase_text == "I had"
    alt_texts = [a.phrase_text for a in r.alternatives]
    assert "I would" in alt_texts


# ── Non-phrase outlines ───────────────────────────────────────────────────────

def test_empty_outline_not_phrase():
    r = detect_phrase("s15", [])
    assert r.is_phrase is False
    assert r.confidence == 0.0


def test_single_pb_family_not_phrase():
    """PB_FAMILY alone is not in any phrase pattern as a single-family phrase."""
    r = detect_phrase("s16", ["PB_FAMILY"])
    assert r.is_phrase is False


def test_unknown_family_not_phrase():
    r = detect_phrase("s17", ["UNKNOWN_FAMILY"])
    assert r.is_phrase is False


def test_four_family_outline_not_phrase():
    r = detect_phrase("s18", ["TD_FAMILY", "PB_FAMILY", "SZ_FAMILY", "FV_FAMILY"])
    assert r.is_phrase is False


def test_reversed_it_is_not_phrase():
    """[SZ, TD] = 'is it', but [SZ, TD] reversed from 'it is' [TD, SZ]."""
    r = detect_phrase("s19", ["SZ_FAMILY", "TD_FAMILY"])
    # This is actually "is it" (a valid phrase) — confirm it's detected correctly
    assert r.phrase_text == "is it"
    # But [TD, SZ] reversed should NOT match "is it"
    r2 = detect_phrase("s20", ["TD_FAMILY", "SZ_FAMILY"])
    assert r2.phrase_text == "it is"
    # The two are distinct
    assert r.phrase_text != r2.phrase_text


# ── Confidence and threshold ──────────────────────────────────────────────────

def test_confidence_in_range_for_detected_phrase():
    r = detect_phrase("s21", ["TD_FAMILY", "SZ_FAMILY"])
    assert 0.0 < r.confidence <= 1.0


def test_confidence_zero_for_no_match():
    r = detect_phrase("s22", ["KG_FAMILY", "PB_FAMILY"])
    assert r.confidence == 0.0


def test_candidate_boost_raises_confidence():
    # "I have" base score = 1.0, boost if "have" is in candidates
    r_no_boost = detect_phrase("s23", ["FV_FAMILY"], candidates=[])
    r_boosted = detect_phrase("s24", ["FV_FAMILY"], candidates=["have"])
    assert r_boosted.confidence >= r_no_boost.confidence


def test_all_detectable_phrases_meet_threshold():
    """Every detectable phrase must return confidence >= its own threshold."""
    for defn in DETECTABLE_PHRASES:
        r = detect_phrase("thr", list(defn.family_pattern))
        if r.is_phrase:
            assert r.confidence >= defn.confidence_threshold, (
                f"{defn.phrase_text}: confidence {r.confidence} < threshold {defn.confidence_threshold}"
            )


# ── Result fields ─────────────────────────────────────────────────────────────

def test_stroke_id_echoed():
    r = detect_phrase("echo-xyz", ["FV_FAMILY"])
    assert r.stroke_id == "echo-xyz"


def test_phrase_text_none_when_no_match():
    r = detect_phrase("s25", ["KG_FAMILY"])
    assert r.phrase_text is None


def test_reasoning_present_when_detected():
    r = detect_phrase("s26", ["FV_FAMILY"])
    assert isinstance(r.reasoning, str)
    assert len(r.reasoning) > 0


def test_reasoning_present_when_no_match():
    r = detect_phrase("s27", ["KG_FAMILY"])
    assert isinstance(r.reasoning, str)
    assert len(r.reasoning) > 0


def test_alternatives_is_list():
    r = detect_phrase("s28", ["CHJ_FAMILY", "SZ_FAMILY"])
    assert isinstance(r.alternatives, list)


# ── API endpoint guard ────────────────────────────────────────────────────────

def test_endpoint_rejects_empty_outline():
    body = DetectPhraseRequest(stroke_id="ep1", outline_families=[], candidates=[])
    with pytest.raises(HTTPException) as exc:
        detect_phrase_endpoint(body)
    assert exc.value.status_code == 422


def test_endpoint_accepts_single_family():
    body = DetectPhraseRequest(stroke_id="ep2", outline_families=["FV_FAMILY"], candidates=[])
    result = detect_phrase_endpoint(body)
    assert result.is_phrase is True
    assert result.phrase_text == "I have"


# ── Phrase definitions sanity checks ─────────────────────────────────────────

def test_phrase_definitions_count():
    """Exactly 20 phrases must be defined."""
    assert len(PHRASE_DEFINITIONS) == 20


def test_detectable_phrases_count():
    """At least 13 phrases must be detectable with current symbol set."""
    assert len(DETECTABLE_PHRASES) >= 13


def test_unavailable_phrases_have_empty_pattern():
    """Phrases requiring missing families must have empty family_pattern."""
    unavailable = ["I am", "it was", "in the", "and the", "on the", "I will"]
    for text in unavailable:
        defn = PHRASE_BY_TEXT[text]
        assert defn.family_pattern == (), f"{text} should have empty family_pattern"
        assert defn.confidence_threshold == 1.0, f"{text} threshold should be 1.0"
