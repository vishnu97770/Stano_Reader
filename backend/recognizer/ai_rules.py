"""
Decision rules for AI-assisted candidate refinement.

All functions are pure — no I/O, no side effects, fully deterministic.
Each rule answers a single yes/no question about whether to invoke AI.

Rules are composed by should_invoke_ai(), the single public entry point
used by the API layer.  Individual rule functions are exported for testing.
"""

from __future__ import annotations

from recognizer.candidate_engine import CandidateResult

# ── Skip rules (each sufficient on its own to skip AI) ──────────────────────


def should_skip_single_high_confidence(
    candidates: list[CandidateResult],
    threshold: float = 0.95,
) -> bool:
    """
    Skip AI when the top candidate has confidence > threshold.

    Rationale: no ambiguity exists; AI cannot meaningfully improve on
    a near-certain deterministic result.
    """
    return bool(candidates) and candidates[0].confidence > threshold


def should_skip_phrase_detected(phrase_detected: bool) -> bool:
    """
    Skip AI when a phraseography match was already found.

    Rationale: the phrase engine has already collapsed a multi-stroke
    outline into a single phrase string; per-word candidate disambiguation
    is irrelevant at this point.
    """
    return phrase_detected


def should_skip_insufficient_context(
    transcript: list[str],
    candidates: list[CandidateResult],
) -> bool:
    """
    Skip AI when the transcript is empty AND there is only one candidate.

    Rationale: with no preceding context and no ambiguity there is nothing
    for the LLM to contribute.
    """
    has_context = any(w.strip() for w in transcript)
    return not has_context and len(candidates) <= 1


def should_skip_no_candidates(candidates: list[CandidateResult]) -> bool:
    """
    Skip AI when no candidates were produced by the deterministic engine.

    Rationale: the LLM cannot re-rank an empty list, and generating
    candidates outside the validated dictionary is not allowed.
    """
    return len(candidates) == 0


# ── Invoke rules (any one sufficient to trigger AI) ──────────────────────────


def should_invoke_ambiguous(
    candidates: list[CandidateResult],
    gap_threshold: float = 0.10,
) -> bool:
    """
    Invoke AI when the top two candidates are within gap_threshold of each other.

    Rationale: close scores mean the deterministic engine is genuinely
    uncertain; context-aware re-ranking can break the tie meaningfully.
    """
    if len(candidates) < 2:
        return False
    return (candidates[0].confidence - candidates[1].confidence) <= gap_threshold


def should_invoke_with_context(transcript: list[str]) -> bool:
    """
    Invoke AI when there is at least one non-empty transcript word.

    Rationale: prior words are the strongest signal for next-word prediction
    and the LLM can use them even when the phoneme match is ambiguous.
    """
    return any(w.strip() for w in transcript)


def should_invoke_with_vowels(vowel_signals: list[str]) -> bool:
    """
    Invoke AI when vowel marks were detected in the stroke.

    Rationale: vowel marks narrow the phonemic space but their IPA meaning
    may have multiple English spellings; the LLM can apply vocabulary
    knowledge to pick the most natural spelling.
    """
    return len(vowel_signals) > 0


# ── Master rule ───────────────────────────────────────────────────────────────


def should_invoke_ai(
    candidates: list[CandidateResult],
    transcript: list[str],
    phrase_detected: bool,
    vowel_signals: list[str],
) -> bool:
    """
    Return True if AI refinement should be attempted for this stroke.

    Evaluation order:
      1. Skip rules — checked first; any match → return False immediately.
      2. Invoke rules — any match → return True.
      3. Default → return False (no reason to incur LLM latency).

    This function is the single gating call used by the API endpoint.
    All constituent rules are independently testable via the functions above.
    """
    # ── Skip gates ────────────────────────────────────────────────────────────
    if should_skip_no_candidates(candidates):
        return False
    if should_skip_single_high_confidence(candidates):
        return False
    if should_skip_phrase_detected(phrase_detected):
        return False
    if should_skip_insufficient_context(transcript, candidates):
        return False

    # ── Invoke gates ──────────────────────────────────────────────────────────
    return (
        should_invoke_ambiguous(candidates)
        or should_invoke_with_context(transcript)
        or should_invoke_with_vowels(vowel_signals)
    )
