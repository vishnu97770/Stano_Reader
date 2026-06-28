"""
AI-assisted candidate refinement engine.

Calls a locally-running Ollama LLM to re-rank word candidates using
transcript context.  The deterministic pipeline always runs first; AI
only adjusts the ordering and never invents new candidates.

All failure modes (timeout, connection refused, parse error, empty response)
are caught silently — the original ranking is returned unchanged.

Public interface
────────────────
    refine_candidates(
        stroke_id, candidates, transcript_context,
        outline, ipa_sequence, domain, vowel_signals
    ) -> AIRefinementResult

    make_fallback_result(stroke_id, candidates, was_invoked, reasoning) -> AIRefinementResult

Background task (used by the API layer)
────────────────────────────────────────
    run_ai_refinement_task(stroke_id, candidates, ..., socket_id) -> Coroutine

Configuration (via environment / .env)
────────────────────────────────────────
    OLLAMA_URL     — default http://localhost:11434/api/generate
    OLLAMA_MODEL   — default llama3.2:1b
    OLLAMA_TIMEOUT — default 3.0 seconds
"""

from __future__ import annotations

import asyncio
import json
import re
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

from recognizer.candidate_engine import CandidateResult
from recognizer.prompt_builder import build_prompt

if TYPE_CHECKING:
    from recognizer.schemas import AIRefinementResult


# ── Defaults (overridden via app/config.py → env vars) ──────────────────────

_DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
_DEFAULT_OLLAMA_MODEL = "llama3.2:1b"
_DEFAULT_TIMEOUT = 3.0

# Module-level config; the API layer injects values from app.config at startup
_ollama_url: str = _DEFAULT_OLLAMA_URL
_ollama_model: str = _DEFAULT_OLLAMA_MODEL
_ollama_timeout: float = _DEFAULT_TIMEOUT


def configure(
    *,
    url: str = _DEFAULT_OLLAMA_URL,
    model: str = _DEFAULT_OLLAMA_MODEL,
    timeout: float = _DEFAULT_TIMEOUT,
) -> None:
    """Inject Ollama configuration from app settings."""
    global _ollama_url, _ollama_model, _ollama_timeout
    _ollama_url = url
    _ollama_model = model
    _ollama_timeout = timeout


# ── Public helpers ────────────────────────────────────────────────────────────


def make_fallback_result(
    stroke_id: str,
    candidates: list[CandidateResult],
    was_invoked: bool = False,
    reasoning: str = "",
) -> "AIRefinementResult":
    """Return an AIRefinementResult that preserves the original ordering."""
    from recognizer.schemas import AIRefinementResult  # local to avoid circular import

    original = [c.word for c in candidates]
    return AIRefinementResult(
        stroke_id=stroke_id,
        was_invoked=was_invoked,
        promoted_candidate=None,
        confidence_boost=0.0,
        reasoning=reasoning,
        original_ranking=original,
        refined_ranking=original,
        fallback_used=True,
        detected=False,
        confidence=0.0,
        alternatives=[],
    )


# ── Synchronous Ollama caller (runs in a thread via asyncio.to_thread) ────────


def _call_ollama_sync(
    stroke_id: str,
    candidates: list[CandidateResult],
    transcript_context: list[str],
    outline: str,
    ipa_sequence: list[str],
    domain: str,
    vowel_signals: list[str],
) -> "AIRefinementResult":
    """
    Call the local Ollama endpoint synchronously.

    Returns a populated AIRefinementResult on success, or a fallback result
    on any error (network, timeout, JSON parse failure, etc.).
    """
    from recognizer.schemas import AIRefinementResult  # local to avoid circular import

    original_ranking = [c.word for c in candidates]

    try:
        prompt = build_prompt(
            candidates=candidates,
            transcript_context=transcript_context,
            outline=outline,
            ipa_sequence=ipa_sequence,
            vowel_signals=vowel_signals,
            domain=domain,
        )

        payload = json.dumps({
            "model": _ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 300},
        }).encode("utf-8")

        req = urllib.request.Request(
            _ollama_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=_ollama_timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        text: str = body.get("response", "")
        if not text.strip():
            return make_fallback_result(
                stroke_id, candidates, was_invoked=True, reasoning="Empty LLM response"
            )

        return _parse_llm_response(stroke_id, text, candidates)

    except (urllib.error.URLError, TimeoutError, OSError):
        return make_fallback_result(
            stroke_id, candidates, was_invoked=True,
            reasoning="Ollama unavailable or timed out"
        )
    except Exception:
        return make_fallback_result(
            stroke_id, candidates, was_invoked=True,
            reasoning="AI refinement error"
        )


def _parse_llm_response(
    stroke_id: str,
    text: str,
    original_candidates: list[CandidateResult],
) -> "AIRefinementResult":
    """
    Extract a JSON array from the LLM response and build AIRefinementResult.

    The LLM may wrap the JSON in prose; we extract the outermost [ … ] block.
    If parsing fails for any reason, returns a fallback result.
    """
    from recognizer.schemas import AIRefinementResult  # local to avoid circular import

    original_ranking = [c.word for c in original_candidates]
    original_conf = {c.word: c.confidence for c in original_candidates}
    known_words = set(original_ranking)

    # Extract JSON array from potentially noisy LLM output
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return make_fallback_result(
            stroke_id, original_candidates, was_invoked=True,
            reasoning="LLM response contained no JSON array"
        )

    try:
        parsed: list[dict] = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return make_fallback_result(
            stroke_id, original_candidates, was_invoked=True,
            reasoning="LLM response JSON was malformed"
        )

    if not isinstance(parsed, list) or not parsed:
        return make_fallback_result(
            stroke_id, original_candidates, was_invoked=True,
            reasoning="LLM returned an empty or non-list JSON structure"
        )

    # Build refined ranking: keep only words that exist in original candidates
    seen: set[str] = set()
    refined_ranking: list[str] = []
    reasoning_map: dict[str, str] = {}

    for item in parsed:
        if not isinstance(item, dict):
            continue
        word = str(item.get("word", "")).strip().lower()
        reason = str(item.get("reason", "")).strip()
        if word and word in known_words and word not in seen:
            refined_ranking.append(word)
            reasoning_map[word] = reason
            seen.add(word)

    # Fallback when the LLM produced zero recognisable words
    if not refined_ranking:
        return make_fallback_result(
            stroke_id, original_candidates, was_invoked=True,
            reasoning="LLM output contained no recognizable candidates"
        )

    # Append any originals the LLM omitted (additive — never removes)
    for w in original_ranking:
        if w not in seen:
            refined_ranking.append(w)

    # Promoted candidate = word at rank 0 in refined list (if different from original)
    top_original = original_ranking[0] if original_ranking else None
    top_refined = refined_ranking[0]
    promoted = top_refined if top_refined != top_original else None

    # Confidence boost for promoted candidate: fixed 0.10
    confidence_boost = 0.10 if promoted else 0.0

    # Primary reasoning: LLM explanation for the top-ranked word
    primary_reasoning = reasoning_map.get(top_refined, "AI re-ranked based on context")

    return AIRefinementResult(
        stroke_id=stroke_id,
        was_invoked=True,
        promoted_candidate=promoted,
        confidence_boost=confidence_boost,
        reasoning=primary_reasoning,
        original_ranking=original_ranking,
        refined_ranking=refined_ranking,
        fallback_used=False,
        detected=True,
        confidence=round(original_conf.get(top_refined, 0.0) + confidence_boost, 4),
        alternatives=[],
    )


# ── Public refine_candidates function ─────────────────────────────────────────


def refine_candidates(
    stroke_id: str,
    candidates: list[CandidateResult],
    transcript_context: list[str],
    outline: str,
    ipa_sequence: list[str],
    domain: str = "general",
    vowel_signals: list[str] | None = None,
) -> "AIRefinementResult":
    """
    Synchronously refine candidates using the local LLM.

    This is the synchronous variant used in tests or when called from a
    non-async context.  Production code uses run_ai_refinement_task (async).
    """
    return _call_ollama_sync(
        stroke_id=stroke_id,
        candidates=candidates,
        transcript_context=transcript_context,
        outline=outline,
        ipa_sequence=ipa_sequence,
        domain=domain,
        vowel_signals=vowel_signals or [],
    )


# ── Async background task (called by the FastAPI API layer) ─────────────────


async def run_ai_refinement_task(
    stroke_id: str,
    candidates: list[CandidateResult],
    transcript_context: list[str],
    outline: str,
    ipa_sequence: list[str],
    domain: str,
    vowel_signals: list[str],
    socket_id: str | None,
) -> None:
    """
    Non-blocking AI refinement task for FastAPI BackgroundTasks.

    Runs the Ollama call in a thread pool (asyncio.to_thread) so the event
    loop stays free during the 3-second timeout window.  Emits the result
    via Socket.IO when done.  All exceptions are caught — failure is silent.
    """
    from app.socket.events import get_sio  # local import to avoid circular

    result = await asyncio.to_thread(
        _call_ollama_sync,
        stroke_id,
        candidates,
        transcript_context,
        outline,
        ipa_sequence,
        domain,
        vowel_signals,
    )

    sio = get_sio()
    if sio is not None and socket_id:
        try:
            await sio.emit("candidates_refined", result.model_dump(), to=socket_id)
        except Exception:
            pass  # Client may have disconnected — ignore silently
