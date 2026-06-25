from pydantic import BaseModel


class TranscriptSaveRequest(BaseModel):
    words: list[str]


class TranscriptSaveResponse(BaseModel):
    saved: bool
