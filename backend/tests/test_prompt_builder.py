"""
Tests for M17 — prompt_builder.py

Coverage (15 tests):
  - Prompt is a non-empty string (1)
  - Role anchor present in all prompts (1)
  - Domain hints for legal, diplomatic, parliamentary (3)
  - General domain produces no special hint (1)
  - Unknown domain falls back gracefully (1)
  - Transcript context included when non-empty (1)
  - Recent 10 words limit respected (1)
  - Empty transcript produces "No prior context" message (1)
  - IPA phoneme sequence included (1)
  - Vowel signals included (1)
  - Outline symbols included (1)
  - Candidates listed with confidence (1)
  - Empty candidates produces empty-array instruction (1)
  - Output instruction present in all prompts (1)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from recognizer.candidate_engine import CandidateResult
from recognizer.prompt_builder import build_prompt


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _candidates(*words: str) -> list[CandidateResult]:
    return [CandidateResult(word=w, confidence=0.8 - i * 0.05) for i, w in enumerate(words)]


# ── Basic output type ─────────────────────────────────────────────────────────


def test_build_prompt_returns_string():
    result = build_prompt(
        candidates=_candidates("give", "get"),
        transcript_context=[],
        outline="P, B",
        ipa_sequence=["/p/", "/b/"],
        vowel_signals=[],
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_role_anchor_present():
    prompt = build_prompt(
        candidates=_candidates("give"),
        transcript_context=[],
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
    )
    assert "Pitman shorthand" in prompt


def test_output_instruction_present():
    prompt = build_prompt(
        candidates=_candidates("give", "get"),
        transcript_context=[],
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
    )
    assert "JSON" in prompt
    assert '[{"word"' in prompt or 'word' in prompt


# ── Domain hints ──────────────────────────────────────────────────────────────


def test_legal_domain_hint_present():
    prompt = build_prompt(
        candidates=_candidates("motion"),
        transcript_context=[],
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
        domain="legal",
    )
    assert "legal" in prompt.lower()
    assert any(kw in prompt.lower() for kw in ("court", "plaintiff", "testimony", "counsel"))


def test_diplomatic_domain_hint_present():
    prompt = build_prompt(
        candidates=_candidates("treaty"),
        transcript_context=[],
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
        domain="diplomatic",
    )
    assert "diplomatic" in prompt.lower()
    assert any(kw in prompt.lower() for kw in ("treaty", "consul", "delegation", "envoy"))


def test_parliamentary_domain_hint_present():
    prompt = build_prompt(
        candidates=_candidates("motion"),
        transcript_context=[],
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
        domain="parliamentary",
    )
    assert "parliamentary" in prompt.lower()
    assert any(kw in prompt.lower() for kw in ("motion", "speaker", "resolution", "committee"))


def test_general_domain_no_special_hint():
    prompt = build_prompt(
        candidates=_candidates("give"),
        transcript_context=[],
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
        domain="general",
    )
    # General mode should not inject legal/diplomatic/parliamentary keywords
    assert "court" not in prompt.lower()
    assert "treaty" not in prompt.lower()
    assert "parliamentary" not in prompt.lower()


def test_unknown_domain_falls_back_gracefully():
    # Should not raise; treats it like general
    prompt = build_prompt(
        candidates=_candidates("give"),
        transcript_context=[],
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
        domain="medical",  # type: ignore[arg-type]
    )
    assert isinstance(prompt, str)


# ── Transcript context ────────────────────────────────────────────────────────


def test_transcript_context_included():
    prompt = build_prompt(
        candidates=_candidates("give"),
        transcript_context=["the", "best"],
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
    )
    assert "the best" in prompt


def test_transcript_context_limited_to_10_words():
    twenty = [f"word{i}" for i in range(20)]
    prompt = build_prompt(
        candidates=_candidates("give"),
        transcript_context=twenty,
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
    )
    # Most recent 10 words should appear; earliest should not
    assert "word19" in prompt
    assert "word0" not in prompt


def test_empty_transcript_produces_no_context_message():
    prompt = build_prompt(
        candidates=_candidates("give"),
        transcript_context=[],
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
    )
    assert "No prior transcript context" in prompt


def test_whitespace_only_transcript_treated_as_empty():
    prompt = build_prompt(
        candidates=_candidates("give"),
        transcript_context=["  ", "\t", ""],
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
    )
    assert "No prior transcript context" in prompt


# ── Phoneme + vowel context ───────────────────────────────────────────────────


def test_ipa_sequence_included():
    prompt = build_prompt(
        candidates=_candidates("give"),
        transcript_context=[],
        outline="",
        ipa_sequence=["/g/", "/v/"],
        vowel_signals=[],
    )
    assert "/g/" in prompt and "/v/" in prompt


def test_vowel_signals_included():
    prompt = build_prompt(
        candidates=_candidates("give"),
        transcript_context=[],
        outline="",
        ipa_sequence=[],
        vowel_signals=["/ɪ/", "/iː/"],
    )
    assert "/ɪ/" in prompt and "/iː/" in prompt


def test_outline_symbols_included():
    prompt = build_prompt(
        candidates=_candidates("give"),
        transcript_context=[],
        outline="G, V",
        ipa_sequence=[],
        vowel_signals=[],
    )
    assert "G, V" in prompt


# ── Candidates ────────────────────────────────────────────────────────────────


def test_candidates_listed_with_confidence():
    prompt = build_prompt(
        candidates=_candidates("give", "get", "go"),
        transcript_context=[],
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
    )
    assert "give" in prompt
    assert "get" in prompt
    assert "go" in prompt
    assert "0." in prompt  # confidence decimal


def test_empty_candidates_produces_empty_array_instruction():
    prompt = build_prompt(
        candidates=[],
        transcript_context=[],
        outline="",
        ipa_sequence=[],
        vowel_signals=[],
    )
    assert "[]" in prompt
