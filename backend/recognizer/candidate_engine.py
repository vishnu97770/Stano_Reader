"""
Deterministic candidate generator.

Takes an ordered phoneme sequence (as produced by the phoneme mapper) and
scores every word in the dictionary by how well the query matches the start
of that word's recognizer-visible consonant skeleton.

Scoring rule
────────────
The query must be a *prefix* of the word's skeleton.  If any query phoneme
differs from the corresponding word phoneme, the score is 0.

When the query IS a valid prefix:
    score = len(query) / len(word_skeleton)

This ranks exact matches (query == skeleton) at 1.0 and rewards words that
are mostly covered by the query over words with many remaining consonants.

Ties are broken alphabetically so output is fully deterministic.
"""

from dataclasses import dataclass

from recognizer.candidate_dictionary import DICTIONARY


@dataclass
class CandidateResult:
    word: str
    confidence: float   # [0, 1]


def _score(query: list[str], skeleton: list[str]) -> float:
    if not query or not skeleton:
        return 0.0
    if len(query) > len(skeleton):
        return 0.0
    for i, q in enumerate(query):
        if skeleton[i] != q:
            return 0.0
    return round(len(query) / len(skeleton), 4)


def get_candidates(phonemes: list[str], max_results: int = 10) -> list[CandidateResult]:
    """
    Return up to max_results candidates for the given phoneme sequence.
    The list is sorted by confidence descending, then alphabetically.
    Duplicate words are deduplicated (first occurrence wins).
    """
    if not phonemes:
        return []

    seen: set[str] = set()
    results: list[CandidateResult] = []

    for word, skeleton in DICTIONARY:
        if word in seen:
            continue
        score = _score(phonemes, skeleton)
        if score > 0.0:
            results.append(CandidateResult(word=word, confidence=score))
            seen.add(word)

    results.sort(key=lambda c: (-c.confidence, c.word))
    return results[:max_results]
