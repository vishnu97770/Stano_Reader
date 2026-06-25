from pydantic import BaseModel, Field


class CandidateRequest(BaseModel):
    phonemes: list[str]           # IPA strings from the phoneme mapper
    max_results: int = Field(default=10, ge=1, le=50)


class CandidateResult(BaseModel):
    word: str
    confidence: float             # [0, 1]


class CandidateResponse(BaseModel):
    candidates: list[CandidateResult]
    query: list[str]              # echo of the input phonemes
