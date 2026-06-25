"""
Context Engine — re-ranks candidates using transcript history.

Public interface
────────────────
    apply_context(transcript, candidates) -> list[ContextCandidateResult]

This is a pure function: same inputs always produce the same outputs.
The current implementation is deterministic and rule-based.

Future AI compatibility
───────────────────────
ContextEngineProtocol defines the structural type any replacement engine must
satisfy.  To swap in an AI engine, implement a callable with the same signature
and pass it wherever apply_context is called.  The API, schemas, and frontend
require no changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from recognizer.candidate_engine import CandidateResult
from recognizer.context_rules import CONTEXT_RULES

_BOOST_CAP = 0.99


@dataclass
class ContextCandidateResult:
    word: str
    confidence: float       # boosted confidence, capped at _BOOST_CAP
    reasoning: str | None   # human-readable; None means no rule fired


class ContextEngineProtocol(Protocol):
    """Structural type for any replacement context engine (rule-based or AI)."""

    def __call__(
        self,
        transcript: list[str],
        candidates: list[CandidateResult],
    ) -> list[ContextCandidateResult]:
        ...


def _last_trigger(transcript: list[str]) -> str | None:
    """Return the last non-empty transcript word, lowercased."""
    for word in reversed(transcript):
        stripped = word.strip().lower()
        if stripped:
            return stripped
    return None


def apply_context(
    transcript: list[str],
    candidates: list[CandidateResult],
) -> list[ContextCandidateResult]:
    """
    Re-rank candidates using the last word of the transcript as a context signal.

    1. Look up the last transcript word in CONTEXT_RULES.
    2. For each candidate, add the rule's boost (if any), cap at 0.99.
    3. Re-sort by boosted confidence descending, then alphabetically.

    When transcript is empty or no rule matches, candidates are returned in
    their original order with reasoning=None.
    """
    trigger = _last_trigger(transcript)
    rule: dict[str, float] = CONTEXT_RULES.get(trigger, {}) if trigger else {}

    results: list[ContextCandidateResult] = []
    for c in candidates:
        boost = rule.get(c.word, 0.0)
        boosted = min(round(c.confidence + boost, 4), _BOOST_CAP)
        if boost > 0.0:
            pct = round(boost * 100)
            reasoning: str | None = f'Boosted +{pct}% after "{trigger}"'
        else:
            reasoning = None
        results.append(ContextCandidateResult(word=c.word, confidence=boosted, reasoning=reasoning))

    results.sort(key=lambda r: (-r.confidence, r.word))
    return results
