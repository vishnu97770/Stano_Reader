from fastapi import APIRouter

from app.schemas.phoneme import PhonemeRequest, PhonemeResponse
from recognizer.phoneme_mapper import map_symbols_to_phonemes

router = APIRouter(prefix="/api", tags=["phoneme"])


@router.post("/phonemes", response_model=PhonemeResponse)
def map_phonemes(body: PhonemeRequest) -> PhonemeResponse:
    inserts = (
        [{"after_index": vi.after_index, "ipa": vi.ipa} for vi in body.vowel_inserts]
        if body.vowel_inserts
        else None
    )
    phonemes = map_symbols_to_phonemes(body.symbols, inserts)
    return PhonemeResponse(phonemes=phonemes)
