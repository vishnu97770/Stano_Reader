"""
Phraseography detector — public API for phrase recognition.

Public function: detect_phrase(stroke_id, outline_families, candidates)

Pipeline:
    outline_families (list of Pitman family names from recognized strokes)
        → score every PhraseDefinition via phrase_rules.score_phrase()
        → collect all matches above their confidence_threshold
        → return the highest-priority match as primary, rest as alternatives

Priority is determined by position in PHRASE_DEFINITIONS (earlier = higher
priority).  This resolves the two collision pairs without discarding the
alternative interpretation.

The function does NOT modify the outline or the candidates list.
"""

from recognizer.phrase_definitions import PHRASE_DEFINITIONS
from recognizer.phrase_rules import build_reasoning, score_phrase
from recognizer.schemas import PhraseMatch, PhraseResult


def detect_phrase(
    stroke_id: str,
    outline_families: list[str],
    candidates: list[str] | None = None,
) -> PhraseResult:
    """
    Detect whether the current outline matches a known Pitman phrase.

    Args:
        stroke_id:       UUID of the most-recently-completed stroke.
        outline_families: Ordered list of Pitman family names for all
                          recognized strokes in the current outline
                          (e.g. ["TD_FAMILY", "SZ_FAMILY"] for "it is").
        candidates:      Current word candidates from the candidate engine.
                         Used only for a small confidence boost; never modified.

    Returns:
        PhraseResult.  When is_phrase=False, phrase_text is None and
        confidence is 0.0.  When is_phrase=True, alternatives contains
        every other phrase that also matched the same outline (sorted
        by confidence desc, then alphabetically).
    """
    _candidates: list[str] = candidates or []

    if not outline_families:
        return PhraseResult(
            stroke_id=stroke_id,
            is_phrase=False,
            phrase_text=None,
            confidence=0.0,
            alternatives=[],
            reasoning="Outline is empty — no phrase can be detected",
        )

    # Score every definition; collect those that meet their own threshold
    matches: list[tuple[float, int, str]] = []  # (score, priority_index, phrase_text)
    for idx, defn in enumerate(PHRASE_DEFINITIONS):
        s = score_phrase(outline_families, defn, _candidates)
        if s >= defn.confidence_threshold:
            matches.append((s, idx, defn.phrase_text))

    if not matches:
        # Build a no-match reasoning referencing the whole outline
        outline_str = " → ".join(outline_families)
        return PhraseResult(
            stroke_id=stroke_id,
            is_phrase=False,
            phrase_text=None,
            confidence=0.0,
            alternatives=[],
            reasoning=f"No phrase pattern matches outline [{outline_str}]",
        )

    # Sort: higher confidence first; ties broken by priority (lower index = higher priority)
    matches.sort(key=lambda t: (-t[0], t[1]))

    best_score, _best_idx, best_text = matches[0]
    best_defn = next(d for d in PHRASE_DEFINITIONS if d.phrase_text == best_text)

    alternatives = [
        PhraseMatch(phrase_text=text, confidence=score)
        for score, _, text in matches[1:]
    ]

    return PhraseResult(
        stroke_id=stroke_id,
        is_phrase=True,
        phrase_text=best_text,
        confidence=best_score,
        alternatives=alternatives,
        reasoning=build_reasoning(outline_families, best_defn, best_score, matched=True),
    )
