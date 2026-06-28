"""
Pitman phraseography definitions — pure data, no logic.

In Pitman shorthand, "phraseography" abbreviates common multi-word phrases into
a single outline.  Each PhraseDefinition maps a phrase to the sequence of Pitman
stroke *families* that form its abbreviated outline.

Matching is family-level (not symbol-level) so that voiced/unvoiced ambiguity
from missing pressure data does not cause false negatives.  For example, "I have"
uses the FV_FAMILY stroke — whether the classifier labels it F or V, the phrase
is still detected.

Phrases whose consonant skeleton requires families not yet implemented
(/m/, /n/, /l/, /w/, /r/) have an empty family_pattern and confidence_threshold
of 1.0 — they can never match with the current symbol set but the architecture
is ready for future milestones.

Priority note: Two collision pairs exist where different phrases share the same
family pattern:
  - [TD_FAMILY]           → "I had" (priority 1), "I would" (priority 2)
  - [FV_FAMILY, THDH_FAMILY] → "of the" (priority 1), "for the" (priority 2)

In these cases the lower-priority phrase appears in PhraseResult.alternatives
rather than as the primary result.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PhraseDefinition:
    phrase_text: str
    ipa_pattern: tuple[str, ...]        # Full IPA of the abbreviated Pitman outline
    family_pattern: tuple[str, ...]     # Ordered Pitman families; empty = not detectable yet
    stroke_description: str             # Human-readable description of the outline
    confidence_threshold: float         # Minimum score to declare a phrase (0–1)


# ---------------------------------------------------------------------------
# 20 common Pitman phrases
#
# Order within this list is the priority for tie-breaking when two phrases
# share the same family_pattern.
# ---------------------------------------------------------------------------

PHRASE_DEFINITIONS: list[PhraseDefinition] = [
    # ── Single-family phrases ────────────────────────────────────────────────

    PhraseDefinition(
        phrase_text="I have",
        ipa_pattern=("/v/",),
        family_pattern=("FV_FAMILY",),
        stroke_description="Single F/V downward curve — 'have' written alone implies 'I'",
        confidence_threshold=0.75,
    ),
    PhraseDefinition(
        phrase_text="I had",
        ipa_pattern=("/d/",),
        family_pattern=("TD_FAMILY",),
        stroke_description="Single T/D diagonal stroke — 'had' written alone implies 'I'",
        confidence_threshold=0.75,
    ),

    # ── Two-family phrases ───────────────────────────────────────────────────

    PhraseDefinition(
        phrase_text="it is",
        ipa_pattern=("/t/", "/z/"),
        family_pattern=("TD_FAMILY", "SZ_FAMILY"),
        stroke_description="T/D diagonal followed by S/Z circle",
        confidence_threshold=0.75,
    ),
    PhraseDefinition(
        phrase_text="to be",
        ipa_pattern=("/t/", "/b/"),
        family_pattern=("TD_FAMILY", "PB_FAMILY"),
        stroke_description="T/D diagonal ('to') joined to P/B downstroke ('be')",
        confidence_threshold=0.75,
    ),
    PhraseDefinition(
        phrase_text="to have",
        ipa_pattern=("/t/", "/v/"),
        family_pattern=("TD_FAMILY", "FV_FAMILY"),
        stroke_description="T/D diagonal ('to') followed by F/V curve ('have')",
        confidence_threshold=0.75,
    ),
    PhraseDefinition(
        phrase_text="of the",
        ipa_pattern=("/v/", "/ð/"),
        family_pattern=("FV_FAMILY", "THDH_FAMILY"),
        stroke_description="F/V curve ('of') followed by TH/DH horizontal ('the')",
        confidence_threshold=0.75,
    ),
    PhraseDefinition(
        phrase_text="at the",
        ipa_pattern=("/t/", "/ð/"),
        family_pattern=("TD_FAMILY", "THDH_FAMILY"),
        stroke_description="T/D diagonal ('at') followed by TH/DH horizontal ('the')",
        confidence_threshold=0.75,
    ),
    PhraseDefinition(
        phrase_text="is it",
        ipa_pattern=("/z/", "/t/"),
        family_pattern=("SZ_FAMILY", "TD_FAMILY"),
        stroke_description="S/Z circle ('is') followed by T/D diagonal ('it')",
        confidence_threshold=0.75,
    ),
    PhraseDefinition(
        phrase_text="there is",
        ipa_pattern=("/ð/", "/z/"),
        family_pattern=("THDH_FAMILY", "SZ_FAMILY"),
        stroke_description="TH/DH horizontal ('there') followed by S/Z circle ('is')",
        confidence_threshold=0.75,
    ),
    PhraseDefinition(
        phrase_text="which is",
        ipa_pattern=("/tʃ/", "/z/"),
        family_pattern=("CHJ_FAMILY", "SZ_FAMILY"),
        stroke_description="CH/J diagonal ('which') followed by S/Z circle ('is')",
        confidence_threshold=0.75,
    ),
    PhraseDefinition(
        phrase_text="as the",
        ipa_pattern=("/z/", "/ð/"),
        family_pattern=("SZ_FAMILY", "THDH_FAMILY"),
        stroke_description="S/Z circle ('as') followed by TH/DH horizontal ('the')",
        confidence_threshold=0.75,
    ),

    # ── Three-family phrases ─────────────────────────────────────────────────

    PhraseDefinition(
        phrase_text="that is",
        ipa_pattern=("/ð/", "/t/", "/z/"),
        family_pattern=("THDH_FAMILY", "TD_FAMILY", "SZ_FAMILY"),
        stroke_description="TH/DH horizontal ('that') + T/D diagonal + S/Z circle ('is')",
        confidence_threshold=0.70,
    ),

    # ── Collision pair 1: "for the" loses to "of the" for [FV, THDH] ────────

    PhraseDefinition(
        phrase_text="for the",
        ipa_pattern=("/f/", "/ð/"),
        family_pattern=("FV_FAMILY", "THDH_FAMILY"),
        stroke_description="F/V curve ('for') followed by TH/DH horizontal ('the') — "
                           "shares pattern with 'of the'; appears as alternative",
        confidence_threshold=0.75,
    ),

    # ── Collision pair 2: "I would" loses to "I had" for [TD] ───────────────

    PhraseDefinition(
        phrase_text="I would",
        ipa_pattern=("/d/",),
        family_pattern=("TD_FAMILY",),
        stroke_description="Single T/D diagonal — 'would' written alone implies 'I'; "
                           "shares pattern with 'I had'; appears as alternative",
        confidence_threshold=0.75,
    ),

    # ── Not yet detectable (require M/N/L/W/R families) ─────────────────────

    PhraseDefinition(
        phrase_text="I am",
        ipa_pattern=("/m/",),
        family_pattern=(),
        stroke_description="M stroke alone — requires M/W family (future milestone)",
        confidence_threshold=1.0,
    ),
    PhraseDefinition(
        phrase_text="it was",
        ipa_pattern=("/t/", "/w/"),
        family_pattern=(),
        stroke_description="T stroke + W upstroke — requires M/W family (future milestone)",
        confidence_threshold=1.0,
    ),
    PhraseDefinition(
        phrase_text="in the",
        ipa_pattern=("/n/", "/ð/"),
        family_pattern=(),
        stroke_description="N stroke + TH/DH — requires N/NG family (future milestone)",
        confidence_threshold=1.0,
    ),
    PhraseDefinition(
        phrase_text="and the",
        ipa_pattern=("/n/", "/d/", "/ð/"),
        family_pattern=(),
        stroke_description="N+D blend + TH/DH — requires N/NG family (future milestone)",
        confidence_threshold=1.0,
    ),
    PhraseDefinition(
        phrase_text="on the",
        ipa_pattern=("/n/", "/ð/"),
        family_pattern=(),
        stroke_description="N stroke + TH/DH — requires N/NG family (future milestone)",
        confidence_threshold=1.0,
    ),
    PhraseDefinition(
        phrase_text="I will",
        ipa_pattern=("/l/",),
        family_pattern=(),
        stroke_description="L stroke alone — requires L/R family (future milestone)",
        confidence_threshold=1.0,
    ),
]

# Lookup by phrase_text for test convenience
PHRASE_BY_TEXT: dict[str, PhraseDefinition] = {
    p.phrase_text: p for p in PHRASE_DEFINITIONS
}

# Detectable phrases (non-empty family_pattern and reachable threshold)
DETECTABLE_PHRASES: list[PhraseDefinition] = [
    p for p in PHRASE_DEFINITIONS if p.family_pattern and p.confidence_threshold < 1.0
]
