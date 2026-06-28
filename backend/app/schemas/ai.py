from typing import Literal

from pydantic import BaseModel, Field


Domain = Literal["general", "legal", "diplomatic", "parliamentary"]


class AICandidateInput(BaseModel):
    word: str
    confidence: float = Field(ge=0.0, le=1.0)


class AIRefinementRequest(BaseModel):
    stroke_id: str
    candidates: list[AICandidateInput]
    transcript_context: list[str] = []
    outline: str = ""
    ipa_sequence: list[str] = []
    domain: Domain = "general"
    vowel_signals: list[str] = []
    phrase_detected: bool = False
    socket_id: str | None = None   # socket.io SID for async push; None = no push
