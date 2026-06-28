from pydantic import BaseModel


class DetectPhraseRequest(BaseModel):
    stroke_id: str
    outline_families: list[str]    # Pitman family names in stroke order
    candidates: list[str] = []    # current top word candidates (for confidence boost)
