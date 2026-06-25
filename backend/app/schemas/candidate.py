from pydantic import BaseModel, Field


class CandidateRequest(BaseModel):
    phonemes: list[str]                        # IPA strings from the phoneme mapper
    transcript: list[str] = []                 # words already accepted into the transcript
    max_results: int = Field(default=10, ge=1, le=50)


class CandidateResult(BaseModel):
    word: str
    confidence: float                          # [0, 1]
    reasoning: str | None = None              # set when a context rule fired


class CandidateResponse(BaseModel):
    candidates: list[CandidateResult]
    query: list[str]                           # echo of the input phonemes
