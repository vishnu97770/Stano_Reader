from fastapi import APIRouter

from app.schemas.candidate import CandidateRequest, CandidateResponse, CandidateResult
from recognizer.candidate_engine import get_candidates
from recognizer.context_engine import apply_context

router = APIRouter(prefix="/api", tags=["candidates"])


@router.post("/candidates", response_model=CandidateResponse)
def get_candidates_endpoint(body: CandidateRequest) -> CandidateResponse:
    raw = get_candidates(body.phonemes, body.max_results)
    contextualized = apply_context(body.transcript, raw)
    candidates = [
        CandidateResult(word=r.word, confidence=r.confidence, reasoning=r.reasoning)
        for r in contextualized
    ]
    return CandidateResponse(candidates=candidates, query=body.phonemes)
