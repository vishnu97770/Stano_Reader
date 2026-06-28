"""
Context Engine — re-ranks candidates using transcript history.

Public interface
────────────────
    apply_context(transcript, candidates, ai_result=None) -> list[ContextCandidateResult]

The core logic is purely deterministic and rule-based.  An optional
``ai_result`` parameter allows the caller to layer AI re-ranking on top
of the rule-based result without changing the existing call sites.

When ``ai_result`` is supplied and ``not ai_result.fallback_used``:
  1.  Rule-based boosting is applied first (unchanged behaviour).
  2.  The AI ranking is then used to re-sort, preserving all candidates
      (AI is additive — it never removes entries).
  3.  The AI-promoted candidate receives a reasoning prefix "✦ AI: …".

Future AI compatibility
───────────────────────
ContextEngineProtocol defines the structural type any replacement engine must
satisfy.  To swap in an AI engine, implement a callable with the same signature
and pass it wherever apply_context is called.  The API, schemas, and frontend
require no changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from recognizer.candidate_engine import CandidateResult
from recognizer.context_rules import CONTEXT_RULES

if TYPE_CHECKING:
    from recognizer.schemas import AIRefinementResult

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
    ai_result: "AIRefinementResult | None" = None,
) -> list[ContextCandidateResult]:
    """
    Re-rank candidates using the last transcript word and optionally AI output.

    Step 1 (always): rule-based boosting via CONTEXT_RULES.
    Step 2 (optional): AI re-ranking when ai_result is provided and valid.

    AI is additive — candidates are never removed, only reordered.
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

    # ── Optional AI re-ranking ────────────────────────────────────────────────
    if (
        ai_result is not None
        and not ai_result.fallback_used
        and ai_result.refined_ranking
    ):
        rank_map = {w: i for i, w in enumerate(ai_result.refined_ranking)}
        results.sort(
            key=lambda r: (rank_map.get(r.word, len(results)), -r.confidence, r.word)
        )
        # Tag the AI-promoted candidate (rank 0 in refined but not in original)
        if ai_result.promoted_candidate:
            for r in results:
                if r.word == ai_result.promoted_candidate:
                    ai_note = f"❆ AI: {ai_result.reasoning}" if ai_result.reasoning else "❆ AI promoted"
                    r.reasoning = (
                        f"{ai_note} | {r.reasoning}" if r.reasoning else ai_note
                    )
                    break

    return results
