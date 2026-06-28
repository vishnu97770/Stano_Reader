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


# IPA vowel phonemes → likely English letter patterns in candidate words.
# Used by boost_by_vowels for deterministic heuristic re-ranking.
_IPA_TO_CHARS: dict[str, list[str]] = {
    "/æ/":  ["a"],
    "/eɪ/": ["a", "ai", "ay"],
    "/ɑː/": ["a", "ar"],
    "/ɛ/":  ["e", "ea"],
    "/ɪ/":  ["i"],
    "/iː/": ["ee", "ie", "ea", "e"],
    "/ʌ/":  ["u", "o"],
    "/ɜː/": ["er", "ur", "ir", "ear"],
    "/ɒ/":  ["o"],
    "/oʊ/": ["o", "oa", "ow"],
    "/ʊ/":  ["oo", "u"],
    "/uː/": ["oo", "u", "ue"],
}

_VOWEL_BOOST = 0.05  # per matched vowel signal


def boost_by_vowels(
    candidates: list[CandidateResult],
    vowel_signals: list[dict],
) -> list[CandidateResult]:
    """
    Re-rank candidates by boosting confidence when a candidate word contains
    letters consistent with detected vowel IPA signals.

    Each entry in vowel_signals must have at least an "ipa" key (str).
    A boost of _VOWEL_BOOST is applied for each signal whose expected letter
    patterns appear anywhere in the candidate word.  Multiple signals
    accumulate.  Confidence is capped at 1.0.

    Returns a new sorted list; the input list is not mutated.
    """
    if not vowel_signals or not candidates:
        return candidates

    boosted: list[CandidateResult] = []
    for c in candidates:
        total_boost = 0.0
        word_lower = c.word.lower()
        for signal in vowel_signals:
            chars = _IPA_TO_CHARS.get(signal.get("ipa", ""), [])
            if any(ch in word_lower for ch in chars):
                total_boost += _VOWEL_BOOST
        new_conf = min(1.0, round(c.confidence + total_boost, 4))
        boosted.append(CandidateResult(word=c.word, confidence=new_conf))

    boosted.sort(key=lambda c: (-c.confidence, c.word))
    return boosted


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
