from pydantic import BaseModel


class VowelInsert(BaseModel):
    after_index: int   # -1 = before first consonant, 0 = after index-0, etc.
    ipa: str           # vowel IPA string, e.g. "/ɪ/"


class PhonemeRequest(BaseModel):
    symbols: list[str]                   # ordered Pitman symbol labels, e.g. ["P", "L", "T"]
    vowel_inserts: list[VowelInsert] = []  # M15.5 — optional vowel injections


class PhonemeResponse(BaseModel):
    phonemes: list[str]  # corresponding IPA strings, e.g. ["/p/", "/l/", "/t/"]
