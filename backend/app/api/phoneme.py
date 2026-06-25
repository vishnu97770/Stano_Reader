from fastapi import APIRouter

from app.schemas.phoneme import PhonemeRequest, PhonemeResponse
from recognizer.phoneme_mapper import map_symbols_to_phonemes

router = APIRouter(prefix="/api", tags=["phoneme"])


@router.post("/phonemes", response_model=PhonemeResponse)
def map_phonemes(body: PhonemeRequest) -> PhonemeResponse:
    phonemes = map_symbols_to_phonemes(body.symbols)
    return PhonemeResponse(phonemes=phonemes)
