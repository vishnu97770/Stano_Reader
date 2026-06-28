"""
AI-assisted candidate refinement endpoint.

POST /api/refine-candidates
  - Checks ai_rules to decide whether to invoke the LLM.
  - Returns immediately with a placeholder AIRefinementResult.
  - Fires a BackgroundTask that calls Ollama asynchronously.
  - When the LLM responds the result is pushed via Socket.IO
    to the requesting client (socket_id field).
  - All failures are silent — fallback_used=True is returned.
"""

from fastapi import APIRouter, BackgroundTasks

from app.schemas.ai import AIRefinementRequest
from recognizer.ai_context_engine import make_fallback_result, run_ai_refinement_task
from recognizer.ai_rules import should_invoke_ai
from recognizer.candidate_engine import CandidateResult
from recognizer.schemas import AIRefinementResult

router = APIRouter(prefix="/api", tags=["ai"])


@router.post("/refine-candidates", response_model=AIRefinementResult)
async def refine_candidates_endpoint(
    body: AIRefinementRequest,
    background_tasks: BackgroundTasks,
) -> AIRefinementResult:
    """
    Non-blocking AI candidate refinement.

    The HTTP response is always immediate.  When the AI call is queued,
    the refined result arrives asynchronously via a ``candidates_refined``
    Socket.IO event emitted to ``body.socket_id``.
    """
    candidates = [
        CandidateResult(word=c.word, confidence=c.confidence)
        for c in body.candidates
    ]

    # Guard: skip AI when rules say there's nothing to be gained
    if not should_invoke_ai(
        candidates,
        body.transcript_context,
        body.phrase_detected,
        body.vowel_signals,
    ):
        return make_fallback_result(
            body.stroke_id,
            candidates,
            was_invoked=False,
            reasoning="Skip rules matched — deterministic result is sufficient",
        )

    # Queue the LLM call as a non-blocking background task
    background_tasks.add_task(
        run_ai_refinement_task,
        body.stroke_id,
        candidates,
        body.transcript_context,
        body.outline,
        body.ipa_sequence,
        body.domain,
        body.vowel_signals,
        body.socket_id,
    )

    # Return immediately with a placeholder; real result arrives via socket
    original = [c.word for c in candidates]
    return AIRefinementResult(
        stroke_id=body.stroke_id,
        was_invoked=True,
        promoted_candidate=None,
        confidence_boost=0.0,
        reasoning="AI refinement queued — result arrives via socket",
        original_ranking=original,
        refined_ranking=original,
        fallback_used=True,
        detected=False,
        confidence=0.0,
        alternatives=[],
    )
