from fastapi import APIRouter, HTTPException

from app.schemas.phrase import DetectPhraseRequest
from recognizer.phrase_detector import detect_phrase
from recognizer.schemas import PhraseResult

router = APIRouter(prefix="/api", tags=["phrase"])


@router.post("/detect-phrase", response_model=PhraseResult)
def detect_phrase_endpoint(body: DetectPhraseRequest) -> PhraseResult:
    # Phrases need at least one recognized stroke in the outline
    if len(body.outline_families) < 1:
        raise HTTPException(
            status_code=422,
            detail="Outline must contain at least 1 recognized stroke family",
        )
    return detect_phrase(body.stroke_id, body.outline_families, body.candidates)
