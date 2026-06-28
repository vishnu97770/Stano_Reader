"""
Tests for M17 — ai_rules.py and ai_context_engine.py

Coverage (30 tests):
  ai_rules (10):
    - skip: high-confidence top candidate (1)
    - skip: phrase detected (1)
    - skip: no context + single candidate (1)
    - skip: empty candidates (1)
    - invoke: ambiguous top-2 (within 0.1) (1)
    - invoke: transcript context available (1)
    - invoke: vowels detected (1)
    - should_invoke_ai: all skip conditions combined (1)
    - should_invoke_ai: invoke when ambiguous + context (1)
    - should_invoke_ai: default no-invoke when no signals (1)

  ai_context_engine — fallback paths (8):
    - fallback on connection refused (1)
    - fallback on timeout error (1)
    - fallback on JSON parse error (1)
    - fallback on empty LLM response (1)
    - fallback when response has no JSON array (1)
    - fallback when all words are unknown (1)
    - original candidates unchanged on fallback (1)
    - make_fallback_result returns correct structure (1)

  ai_context_engine — success paths (7):
    - valid LLM response → refined_ranking matches (1)
    - promoted_candidate detected correctly (1)
    - confidence_boost is 0.10 for promoted (1)
    - was_invoked=True on success (1)
    - detected=True on success (1)
    - fallback_used=False on success (1)
    - reasoning matches LLM output (1)

  ai_context_engine — edge cases (5):
    - LLM response with prose around JSON (1)
    - partial candidate list from LLM gets original appended (1)
    - AIRefinementResult schema validates (1)
    - context_engine apply_context with ai_result integration (1)
    - context_engine apply_context unchanged without ai_result (1)
"""

import json
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from recognizer.ai_context_engine import (
    _call_ollama_sync,
    _parse_llm_response,
    make_fallback_result,
)
from recognizer.ai_rules import (
    should_invoke_ai,
    should_invoke_ambiguous,
    should_invoke_with_context,
    should_invoke_with_vowels,
    should_skip_insufficient_context,
    should_skip_no_candidates,
    should_skip_phrase_detected,
    should_skip_single_high_confidence,
)
from recognizer.candidate_engine import CandidateResult
from recognizer.context_engine import apply_context
from recognizer.schemas import AIRefinementResult


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _c(*pairs: tuple) -> list[CandidateResult]:
    return [CandidateResult(word=w, confidence=c) for w, c in pairs]


def _high() -> list[CandidateResult]:
    return _c(("give", 0.96), ("get", 0.50))


def _ambiguous() -> list[CandidateResult]:
    return _c(("give", 0.75), ("get", 0.70), ("go", 0.40))


def _single() -> list[CandidateResult]:
    return _c(("give", 0.70),)


def _mock_ollama_response(words: list[str]) -> MagicMock:
    """Build a mock for urllib.request.urlopen returning a valid LLM JSON response."""
    payload = json.dumps([{"word": w, "reason": f"reason for {w}"} for w in words])
    ollama_resp = json.dumps({"response": payload, "done": True}).encode()
    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read.return_value = ollama_resp
    return mock_resp


# ── ai_rules: skip conditions ─────────────────────────────────────────────────


def test_skip_high_confidence():
    assert should_skip_single_high_confidence(_high()) is True


def test_no_skip_moderate_confidence():
    assert should_skip_single_high_confidence(_ambiguous()) is False


def test_skip_phrase_detected_true():
    assert should_skip_phrase_detected(True) is True


def test_no_skip_phrase_not_detected():
    assert should_skip_phrase_detected(False) is False


def test_skip_insufficient_context_empty_transcript_single_candidate():
    assert should_skip_insufficient_context([], _single()) is True


def test_no_skip_when_transcript_available():
    assert should_skip_insufficient_context(["the"], _single()) is False


def test_skip_no_candidates():
    assert should_skip_no_candidates([]) is True


def test_no_skip_when_candidates_present():
    assert should_skip_no_candidates(_ambiguous()) is False


# ── ai_rules: invoke conditions ───────────────────────────────────────────────


def test_invoke_ambiguous_within_threshold():
    assert should_invoke_ambiguous(_ambiguous()) is True


def test_no_invoke_clear_winner():
    assert should_invoke_ambiguous(_c(("give", 0.90), ("get", 0.70))) is False


def test_invoke_with_transcript_context():
    assert should_invoke_with_context(["the"]) is True


def test_no_invoke_empty_transcript():
    assert should_invoke_with_context([]) is False


def test_invoke_with_vowels():
    assert should_invoke_with_vowels(["/æ/"]) is True


def test_no_invoke_no_vowels():
    assert should_invoke_with_vowels([]) is False


# ── ai_rules: master rule ─────────────────────────────────────────────────────


def test_should_invoke_ai_returns_false_when_high_confidence():
    assert should_invoke_ai(_high(), ["the"], False, []) is False


def test_should_invoke_ai_returns_false_when_phrase_detected():
    assert should_invoke_ai(_ambiguous(), ["the"], True, []) is False


def test_should_invoke_ai_returns_true_when_ambiguous_with_context():
    assert should_invoke_ai(_ambiguous(), ["the"], False, []) is True


def test_should_invoke_ai_returns_false_when_no_signals():
    # No context, no vowels, single clear candidate
    assert should_invoke_ai(_single(), [], False, []) is False


# ── make_fallback_result ──────────────────────────────────────────────────────


def test_make_fallback_result_structure():
    result = make_fallback_result("s1", _ambiguous(), was_invoked=False, reasoning="test")
    assert isinstance(result, AIRefinementResult)
    assert result.fallback_used is True
    assert result.was_invoked is False
    assert result.detected is False
    assert result.refined_ranking == result.original_ranking
    assert result.promoted_candidate is None
    assert result.confidence_boost == 0.0


def test_make_fallback_result_original_order_preserved():
    candidates = _c(("give", 0.8), ("get", 0.7), ("go", 0.5))
    result = make_fallback_result("s1", candidates)
    assert result.original_ranking == ["give", "get", "go"]
    assert result.refined_ranking == ["give", "get", "go"]


# ── _call_ollama_sync: fallback paths ────────────────────────────────────────


def test_fallback_on_connection_refused():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        result = _call_ollama_sync("s1", _ambiguous(), [], "", [], "general", [])
    assert result.fallback_used is True
    assert result.was_invoked is True


def test_fallback_on_timeout():
    with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
        result = _call_ollama_sync("s1", _ambiguous(), [], "", [], "general", [])
    assert result.fallback_used is True
    assert result.was_invoked is True


def test_fallback_on_json_parse_error():
    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    # Ollama response body is valid JSON but the LLM response field is not
    mock_resp.read.return_value = json.dumps({"response": "not json at all", "done": True}).encode()
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", _ambiguous(), [], "", [], "general", [])
    assert result.fallback_used is True


def test_fallback_on_empty_llm_response():
    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read.return_value = json.dumps({"response": "", "done": True}).encode()
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", _ambiguous(), [], "", [], "general", [])
    assert result.fallback_used is True


def test_fallback_when_response_has_no_array():
    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read.return_value = json.dumps({"response": "The best word is give.", "done": True}).encode()
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", _ambiguous(), [], "", [], "general", [])
    assert result.fallback_used is True


def test_fallback_when_all_llm_words_unknown():
    mock_resp = _mock_ollama_response(["unknown1", "unknown2"])
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", _ambiguous(), [], "", [], "general", [])
    assert result.fallback_used is True


# ── _call_ollama_sync: success paths ─────────────────────────────────────────


def test_success_refined_ranking_matches_llm_order():
    candidates = _c(("give", 0.75), ("get", 0.70))
    mock_resp = _mock_ollama_response(["get", "give"])
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", candidates, [], "", [], "general", [])
    assert result.refined_ranking == ["get", "give"]
    assert result.fallback_used is False


def test_success_promoted_candidate_correct():
    candidates = _c(("give", 0.75), ("get", 0.70))
    mock_resp = _mock_ollama_response(["get", "give"])
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", candidates, [], "", [], "general", [])
    assert result.promoted_candidate == "get"


def test_success_confidence_boost_is_010():
    candidates = _c(("give", 0.75), ("get", 0.70))
    mock_resp = _mock_ollama_response(["get", "give"])
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", candidates, [], "", [], "general", [])
    assert result.confidence_boost == 0.10


def test_success_was_invoked_true():
    candidates = _c(("give", 0.75), ("get", 0.70))
    mock_resp = _mock_ollama_response(["give", "get"])
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", candidates, [], "", [], "general", [])
    assert result.was_invoked is True


def test_success_detected_true():
    candidates = _c(("give", 0.75), ("get", 0.70))
    mock_resp = _mock_ollama_response(["give", "get"])
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", candidates, [], "", [], "general", [])
    assert result.detected is True


def test_success_fallback_false():
    candidates = _c(("give", 0.75), ("get", 0.70))
    mock_resp = _mock_ollama_response(["give", "get"])
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", candidates, [], "", [], "general", [])
    assert result.fallback_used is False


def test_success_reasoning_from_llm():
    candidates = _c(("give", 0.75), ("get", 0.70))
    payload = json.dumps([{"word": "give", "reason": "verb after I"}, {"word": "get", "reason": "alternative"}])
    mock_body = json.dumps({"response": payload, "done": True}).encode()
    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read.return_value = mock_body
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", candidates, [], "", [], "general", [])
    assert "verb after I" in result.reasoning


# ── Edge cases ────────────────────────────────────────────────────────────────


def test_llm_response_with_prose_around_json():
    candidates = _c(("give", 0.75), ("get", 0.70))
    inner = json.dumps([{"word": "get", "reason": "best fit"}, {"word": "give", "reason": "alternative"}])
    # Wrap JSON in surrounding prose (common LLM behaviour)
    llm_text = f"Sure! Here is my ranking:\n{inner}\nI hope that helps."
    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read.return_value = json.dumps({"response": llm_text, "done": True}).encode()
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", candidates, [], "", [], "general", [])
    assert result.fallback_used is False
    assert result.refined_ranking[0] == "get"


def test_partial_llm_list_appends_missing_originals():
    candidates = _c(("give", 0.75), ("get", 0.70), ("go", 0.50))
    # LLM only returns 2 out of 3
    mock_resp = _mock_ollama_response(["get", "give"])
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _call_ollama_sync("s1", candidates, [], "", [], "general", [])
    # "go" must still be present (additive — never removes)
    assert "go" in result.refined_ranking
    assert len(result.refined_ranking) == 3


def test_ai_refinement_result_schema_validates():
    result = AIRefinementResult(
        stroke_id="s1",
        was_invoked=True,
        promoted_candidate="give",
        confidence_boost=0.1,
        reasoning="context",
        original_ranking=["get", "give"],
        refined_ranking=["give", "get"],
        fallback_used=False,
        detected=True,
        confidence=0.85,
    )
    assert result.stroke_id == "s1"
    assert result.alternatives == []


# ── context_engine integration ────────────────────────────────────────────────


def test_apply_context_unchanged_without_ai_result():
    raw = [CandidateResult(word="give", confidence=0.8)]
    results = apply_context(["i"], raw, ai_result=None)
    assert results[0].word == "give"


def test_apply_context_with_ai_result_reorders():
    raw = [
        CandidateResult(word="give", confidence=0.8),
        CandidateResult(word="get", confidence=0.75),
    ]
    ai = AIRefinementResult(
        stroke_id="s1",
        was_invoked=True,
        promoted_candidate="get",
        confidence_boost=0.1,
        reasoning="better fit",
        original_ranking=["give", "get"],
        refined_ranking=["get", "give"],
        fallback_used=False,
        detected=True,
        confidence=0.85,
    )
    results = apply_context([], raw, ai_result=ai)
    assert results[0].word == "get"
