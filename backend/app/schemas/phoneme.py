from pydantic import BaseModel


class PhonemeRequest(BaseModel):
    symbols: list[str]   # ordered Pitman symbol labels, e.g. ["P", "L", "T"]


class PhonemeResponse(BaseModel):
    phonemes: list[str]  # corresponding IPA strings, e.g. ["/p/", "/l/", "/t/"]
