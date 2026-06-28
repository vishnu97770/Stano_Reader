"""
Phraseography matching rules — pure functions, no side effects.

All functions are independent and testable in isolation.  No imports from
detector or API layers; only definitions and schemas.

Rule overview
─────────────
1.  match_phrase()     — structural: does the outline's family sequence match
                         this phrase's family_pattern exactly?
2.  candidate_boost()  — contextual: do the current word candidates suggest
                         a word from this phrase is already in play?
3.  score_phrase()     — combined: structural score + candidate boost, capped at 1.0
"""

from recognizer.phrase_definitions import PhraseDefinition

# Maximum confidence bonus from candidate agreement
CANDIDATE_BOOST_MAX: float = 0.10


def match_phrase(
    outline_families: list[str],
    definition: PhraseDefinition,
) -> float:
    """
    Return 1.0 if outline_families exactly matches definition.family_pattern,
    otherwise 0.0.

    Exact match is intentional: phrases are a complete outline (the writer
    draws *only* the phrase strokes, nothing else).  Partial matches would
    fire on every opening stroke.

    Empty family_pattern (undetectable phrase) always returns 0.0.
    """
    if not definition.family_pattern:
        return 0.0
    if len(outline_families) != len(definition.family_pattern):
        return 0.0
    for family, expected in zip(outline_families, definition.family_pattern):
        if family != expected:
            return 0.0
    return 1.0


def candidate_boost(
    definition: PhraseDefinition,
    candidates: list[str],
) -> float:
    """
    Return a small confidence boost when a content word from the phrase
    appears in the current candidate list.

    The last word of the phrase is the most likely candidate word
    (e.g. "have" for "I have", "the" for "of the").

    Returns 0.0 when candidates is empty or no word matches.
    Returns at most CANDIDATE_BOOST_MAX.
    """
    if not candidates or not definition.phrase_text:
        return 0.0
    phrase_words = definition.phrase_text.lower().split()
    candidate_set = {c.lower() for c in candidates}
    for word in reversed(phrase_words):
        if word in candidate_set:
            return CANDIDATE_BOOST_MAX
    return 0.0


def score_phrase(
    outline_families: list[str],
    definition: PhraseDefinition,
    candidates: list[str],
) -> float:
    """
    Combined phrase score: structural match + candidate agreement, capped at 1.0.

    Returns 0.0 when there is no structural match regardless of candidates.
    Returns >= confidence_threshold when the phrase should fire.
    """
    base = match_phrase(outline_families, definition)
    if base == 0.0:
        return 0.0
    boost = candidate_boost(definition, candidates)
    return round(min(1.0, base + boost), 4)


def build_reasoning(
    outline_families: list[str],
    definition: PhraseDefinition,
    score: float,
    matched: bool,
) -> str:
    """
    Human-readable explanation of the phrase detection outcome.
    Called for both matched and non-matched cases.
    """
    pattern_str = " → ".join(definition.family_pattern) if definition.family_pattern else "∅"
    outline_str = " → ".join(outline_families) if outline_families else "∅"

    if matched:
        return (
            f"Outline [{outline_str}] matches '{definition.phrase_text}' "
            f"(pattern: [{pattern_str}]); confidence={score:.2f}"
        )
    if not outline_families:
        return "Outline is empty — no phrase can be detected"
    if not definition.family_pattern:
        return (
            f"'{definition.phrase_text}' requires families not yet implemented; "
            f"outline was [{outline_str}]"
        )
    return (
        f"No phrase pattern matches outline [{outline_str}]; "
        f"closest checked: '{definition.phrase_text}' expected [{pattern_str}]"
    )
