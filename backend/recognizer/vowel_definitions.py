"""
Pitman shorthand vowel sign definitions.

Pitman uses 12 vowel signs arranged across 3 degrees (positional rows relative
to the consonant stroke) and 4 mark types (dot/dash × before/after the stroke).

Degree determines vertical position relative to the consonant:
  1 — near the start (top) of the stroke
  2 — near the middle of the stroke
  3 — near the end (bottom) of the stroke

Position determines reading-order placement:
  "before" — the vowel precedes the consonant in reading order (written to the
              left for vertical strokes, above for horizontal strokes)
  "after"  — the vowel follows the consonant (written to the right or below)

Mark type:
  "dot"  — a small stationary point; bounding box < DOT_MAX_PX on both axes
  "dash" — a short directed stroke; path length between DOT_MAX_PX and DASH_MAX_PX
"""

from dataclasses import dataclass


# ── Size thresholds (canvas pixels) ──────────────────────────────────────────

DOT_MAX_PX: float = 10.0    # bounding box dimension; dots are smaller than this
DASH_MAX_PX: float = 28.0   # path length upper bound for dash marks
PROXIMITY_PX: float = 80.0  # max distance from vowel centroid to consonant centroid


# ── Definition dataclass ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class VowelDefinition:
    symbol: str          # unique label, e.g. "DOT1_BEFORE"
    ipa: str             # IPA phoneme string, e.g. "/æ/"
    degree: int          # 1, 2, or 3
    position: str        # "before" | "after"
    mark: str            # "dot" | "dash"
    example: str         # English example word for the vowel sound


# ── 12 Pitman vowel signs ─────────────────────────────────────────────────────
# Row order: degree 1 → 2 → 3, within each row: dot-before, dot-after,
# dash-before, dash-after.

VOWEL_DEFINITIONS: list[VowelDefinition] = [
    # Degree 1 — placed near the START of the consonant stroke
    VowelDefinition(symbol="DOT1_BEFORE",  ipa="/æ/",  degree=1, position="before", mark="dot",  example="cat"),
    VowelDefinition(symbol="DOT1_AFTER",   ipa="/eɪ/", degree=1, position="after",  mark="dot",  example="name"),
    VowelDefinition(symbol="DASH1_BEFORE", ipa="/ɑː/", degree=1, position="before", mark="dash", example="father"),
    VowelDefinition(symbol="DASH1_AFTER",  ipa="/ɛ/",  degree=1, position="after",  mark="dash", example="bed"),

    # Degree 2 — placed near the MIDDLE of the consonant stroke
    VowelDefinition(symbol="DOT2_BEFORE",  ipa="/ɪ/",  degree=2, position="before", mark="dot",  example="bit"),
    VowelDefinition(symbol="DOT2_AFTER",   ipa="/iː/", degree=2, position="after",  mark="dot",  example="see"),
    VowelDefinition(symbol="DASH2_BEFORE", ipa="/ʌ/",  degree=2, position="before", mark="dash", example="cut"),
    VowelDefinition(symbol="DASH2_AFTER",  ipa="/ɜː/", degree=2, position="after",  mark="dash", example="her"),

    # Degree 3 — placed near the END of the consonant stroke
    VowelDefinition(symbol="DOT3_BEFORE",  ipa="/ɒ/",  degree=3, position="before", mark="dot",  example="hot"),
    VowelDefinition(symbol="DOT3_AFTER",   ipa="/oʊ/", degree=3, position="after",  mark="dot",  example="go"),
    VowelDefinition(symbol="DASH3_BEFORE", ipa="/ʊ/",  degree=3, position="before", mark="dash", example="book"),
    VowelDefinition(symbol="DASH3_AFTER",  ipa="/uː/", degree=3, position="after",  mark="dash", example="food"),
]

# Lookup by symbol name
VOWEL_BY_SYMBOL: dict[str, VowelDefinition] = {v.symbol: v for v in VOWEL_DEFINITIONS}

# Lookup by (degree, position, mark) — the natural key from detection results
VOWEL_BY_KEY: dict[tuple[int, str, str], VowelDefinition] = {
    (v.degree, v.position, v.mark): v for v in VOWEL_DEFINITIONS
}
