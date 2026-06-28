"""
Canonical stroke length definitions for Pitman halving and doubling detection.

Lengths are in canvas pixels and represent the typical path length of a normal
stroke drawn on an ~1200×800 canvas.  Vertical strokes are drawn longest;
near-horizontal strokes are drawn shorter for the same perceived visual size.

SZ_FAMILY is excluded (circles/loops do not participate in halving/doubling).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LengthDefinition:
    family_name: str
    canonical_px: float          # expected length of a normal stroke in this family
    half_phoneme: str            # IPA phoneme added when stroke is halved
    double_phoneme: str          # IPA phoneme added when stroke is doubled
    description: str


LENGTH_DEFINITIONS: dict[str, LengthDefinition] = {
    "PB_FAMILY": LengthDefinition(
        family_name="PB_FAMILY",
        canonical_px=100.0,
        half_phoneme="/t/",
        double_phoneme="/r/",
        description="Near-vertical downstroke — drawn tallest",
    ),
    "TD_FAMILY": LengthDefinition(
        family_name="TD_FAMILY",
        canonical_px=90.0,
        half_phoneme="/t/",
        double_phoneme="/r/",
        description="45° down-right diagonal",
    ),
    "KG_FAMILY": LengthDefinition(
        family_name="KG_FAMILY",
        canonical_px=80.0,
        half_phoneme="/t/",
        double_phoneme="/r/",
        description="Near-horizontal rightward stroke — drawn shorter",
    ),
    "CHJ_FAMILY": LengthDefinition(
        family_name="CHJ_FAMILY",
        canonical_px=90.0,
        half_phoneme="/t/",
        double_phoneme="/r/",
        description="45° down-left diagonal",
    ),
    "FV_FAMILY": LengthDefinition(
        family_name="FV_FAMILY",
        canonical_px=90.0,
        half_phoneme="/t/",
        double_phoneme="/r/",
        description="Steeper down-left stroke",
    ),
    "THDH_FAMILY": LengthDefinition(
        family_name="THDH_FAMILY",
        canonical_px=80.0,
        half_phoneme="/t/",
        double_phoneme="/r/",
        description="Near-flat horizontal stroke — drawn shorter",
    ),
    "SHZH_FAMILY": LengthDefinition(
        family_name="SHZH_FAMILY",
        canonical_px=90.0,
        half_phoneme="/t/",
        double_phoneme="/r/",
        description="Upstroke",
    ),
    # SZ_FAMILY intentionally omitted — circles do not use halving/doubling
}

# Fallback when family is unknown or not provided
GLOBAL_CANONICAL_PX: float = 90.0

# IPA phonemes for the family-agnostic fallback
GLOBAL_HALF_PHONEME: str = "/t/"
GLOBAL_DOUBLE_PHONEME: str = "/r/"
