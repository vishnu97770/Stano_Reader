"""
Pitman shorthand circle and loop definitions — pure data, no logic.

In Pitman shorthand, circles and loops are not standalone strokes — they join
adjacent consonant strokes.  For this milestone we treat them as standalone
stroke types and identify their primary phoneme representation.

position="ANY" is a placeholder for future milestone that distinguishes:
  "INITIAL"  — circle/loop at the start of an outline
  "MEDIAL"   — circle/loop between two consonants
  "FINAL"    — circle/loop at the end of an outline

Adding position rules only requires new entries here and in circle_rules.py.
No other file needs to change.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CircleDefinition:
    name: str           # "SMALL_CIRCLE" | "LARGE_CIRCLE" | "SMALL_LOOP" | "LARGE_LOOP"
    phoneme: str        # primary IPA phoneme this form represents
    description: str
    is_loop: bool       # False = circle; True = elongated loop
    is_large: bool      # False = small variant; True = large variant
    position: str       # "ANY" for now; future: "INITIAL" | "MEDIAL" | "FINAL"


CIRCLE_DEFINITIONS: dict[str, CircleDefinition] = {
    "SMALL_CIRCLE": CircleDefinition(
        name="SMALL_CIRCLE",
        phoneme="/s/",
        description="Small circle: represents S/Z in joining position",
        is_loop=False,
        is_large=False,
        position="ANY",
    ),
    "LARGE_CIRCLE": CircleDefinition(
        name="LARGE_CIRCLE",
        phoneme="/sw/",
        description="Large circle: represents SW or WH combination",
        is_loop=False,
        is_large=True,
        position="ANY",
    ),
    "SMALL_LOOP": CircleDefinition(
        name="SMALL_LOOP",
        phoneme="/ns/",
        description="Small loop: represents NS/NZ combination",
        is_loop=True,
        is_large=False,
        position="ANY",
    ),
    "LARGE_LOOP": CircleDefinition(
        name="LARGE_LOOP",
        phoneme="/ls/",
        description="Large loop: represents LS/LZ combination",
        is_loop=True,
        is_large=True,
        position="ANY",
    ),
}

# Ordered list for deterministic iteration
ALL_CIRCLE_TYPES: list[str] = list(CIRCLE_DEFINITIONS.keys())
