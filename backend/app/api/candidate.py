from fastapi import APIRouter

from app.schemas.candidate import CandidateRequest, CandidateResponse, CandidateResult
from recognizer.candidate_engine import get_candidates

router = APIRouter(prefix="/api", tags=["candidates"])


@router.post("/candidates", response_model=CandidateResponse)
def get_candidates_endpoint(body: CandidateRequest) -> CandidateResponse:
    results = get_candidates(body.phonemes, body.max_results)
    candidates = [CandidateResult(word=r.word, confidence=r.confidence) for r in results]
    return CandidateResponse(candidates=candidates, query=body.phonemes)
