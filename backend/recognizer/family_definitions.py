"""
Pitman shorthand family definitions — pure data, no logic.

Each FamilyDefinition describes the geometric signature of one family of
Pitman consonant strokes.  Families group strokes that differ only by
pressure (voiced vs unvoiced), which we cannot detect without a pressure
sensor.

Canvas coordinate system: Y increases downward, X increases rightward.
Angles: 0° = rightward, 90° = downward, 180° = leftward, 270° = upward.

Adding a new family requires only a new entry in FAMILY_DEFINITIONS.
No logic in family_rules.py or family_classifier.py needs to change.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FamilyDefinition:
    name: str
    members: tuple[str, ...]       # Pitman phoneme symbols in this family
    angle_center: float            # Expected start-to-end bearing (degrees)
    angle_tolerance: float         # Degrees from center where score reaches 0
    expect_curve: bool             # False = straight stroke; True = curved/circle
    aspect_hint: str               # "tall" | "wide" | "balanced" | "square"
    description: str


# ---------------------------------------------------------------------------
# 8 Pitman families for Milestone 5
# ---------------------------------------------------------------------------
# Straight-stroke families are discriminated primarily by angle.
# SZ_FAMILY is unique: it is a small looping circle (is_curve=True, high ratio).
# SHZH_FAMILY is the only upstroke (angles 270-320°).
#
# Angle reference:
#   PB   90°  — vertical downstroke
#   TD   50°  — 45° diagonal down-right
#   KG   20°  — near-horizontal right (gentle slope)
#   CHJ 130°  — 45° diagonal down-left (mirror of TD)
#   FV  155°  — steeper down-left (between CHJ and horizontal-left)
#   THDH  0°  — near-flat horizontal left-to-right (wraps at 360°)
#   SZ   N/A  — small loop / circle
#   SHZH 290° — upstroke (up / up-right)
# ---------------------------------------------------------------------------

FAMILY_DEFINITIONS: dict[str, FamilyDefinition] = {
    "PB_FAMILY": FamilyDefinition(
        name="PB_FAMILY",
        members=("P", "B"),
        angle_center=90.0,
        angle_tolerance=22.0,
        expect_curve=False,
        aspect_hint="tall",
        description="Near-vertical downstroke (P light, B heavy)",
    ),
    "TD_FAMILY": FamilyDefinition(
        name="TD_FAMILY",
        members=("T", "D"),
        angle_center=50.0,
        angle_tolerance=22.0,
        expect_curve=False,
        aspect_hint="balanced",
        description="45° down-right diagonal (T light, D heavy)",
    ),
    "KG_FAMILY": FamilyDefinition(
        name="KG_FAMILY",
        members=("K", "G"),
        angle_center=20.0,
        angle_tolerance=22.0,
        expect_curve=False,
        aspect_hint="wide",
        description="Near-horizontal rightward stroke with gentle slope (K light, G heavy)",
    ),
    "CHJ_FAMILY": FamilyDefinition(
        name="CHJ_FAMILY",
        members=("CH", "J"),
        angle_center=130.0,
        angle_tolerance=22.0,
        expect_curve=False,
        aspect_hint="balanced",
        description="45° down-left diagonal, mirror of TD (CH light, J heavy)",
    ),
    "FV_FAMILY": FamilyDefinition(
        name="FV_FAMILY",
        members=("F", "V"),
        angle_center=155.0,
        angle_tolerance=22.0,
        expect_curve=False,
        aspect_hint="balanced",
        description="Steeper down-left stroke, between CHJ and horizontal (F light, V heavy)",
    ),
    "THDH_FAMILY": FamilyDefinition(
        name="THDH_FAMILY",
        members=("TH", "DH"),
        angle_center=0.0,     # wraps at 360°; handled by circular diff in rules
        angle_tolerance=18.0,
        expect_curve=False,
        aspect_hint="wide",
        description="Near-flat horizontal left-to-right stroke (TH light, DH heavy)",
    ),
    "SZ_FAMILY": FamilyDefinition(
        name="SZ_FAMILY",
        members=("S", "Z"),
        angle_center=0.0,     # irrelevant — scoring uses curvature, not angle
        angle_tolerance=360.0,  # all angles accepted (it's a circle)
        expect_curve=True,
        aspect_hint="square",
        description="Small looping circle/oval (S light, Z heavy)",
    ),
    "SHZH_FAMILY": FamilyDefinition(
        name="SHZH_FAMILY",
        members=("SH", "ZH"),
        angle_center=290.0,
        angle_tolerance=28.0,
        expect_curve=False,
        aspect_hint="balanced",
        description="Upstroke going upward or up-right (SH light, ZH heavy)",
    ),
    # ── M19: Nine new consonant families ────────────────────────────────────────
    #
    # Angle coverage of the existing 8 families (straight strokes):
    #   THDH  0° ±18°  = [342°, 18°]
    #   KG   20° ±22°  = [0°, 42°]
    #   TD   50° ±22°  = [28°, 72°]
    #   PB   90° ±22°  = [68°, 112°]
    #   CHJ 130° ±22°  = [108°, 152°]
    #   FV  155° ±22°  = [133°, 177°]
    #   SHZH 290° ±28° = [262°, 318°]
    #
    # Free straight-stroke gaps: [177°, 262°] and [318°, 342°].
    # New curved-stroke families (MW, NN, Y) exploit is_curve=True to avoid
    # conflicting with straight-stroke families at the same angle.
    # ────────────────────────────────────────────────────────────────────────────
    "MW_FAMILY": FamilyDefinition(
        name="MW_FAMILY",
        members=("M", "W"),
        angle_center=0.0,
        angle_tolerance=35.0,
        expect_curve=True,    # open rightward arc; THDH/KG are straight at same angle
        aspect_hint="wide",
        description="Curved rightward arc (M large/long, W small/short)",
    ),
    "LR_FAMILY": FamilyDefinition(
        name="LR_FAMILY",
        members=("L", "R"),
        angle_center=325.0,   # up-right; gap between SHZH (max 318°) and THDH (min 342°)
        angle_tolerance=20.0,
        expect_curve=False,   # L is straight; R is curved — handled via special case in rules
        aspect_hint="balanced",
        description="Up-right upstroke (L straight, R curved — same direction, scored by angle)",
    ),
    "NN_FAMILY": FamilyDefinition(
        name="NN_FAMILY",
        members=("N", "NG", "NK"),
        angle_center=90.0,    # downward; PB is straight at same angle — curvature separates them
        angle_tolerance=25.0,
        expect_curve=True,    # open downward arc; PB at 90° is always straight
        aspect_hint="tall",
        description="Curved downward stroke (N short, NG long, NK with hook)",
    ),
    "Y_FAMILY": FamilyDefinition(
        name="Y_FAMILY",
        members=("Y",),
        angle_center=200.0,   # down-left; free gap beyond FV (max 177°)
        angle_tolerance=30.0,
        expect_curve=True,    # small curved hook
        aspect_hint="balanced",
        description="Small curved down-left hook stroke (Y = /j/)",
    ),
    "H_FAMILY": FamilyDefinition(
        name="H_FAMILY",
        members=("H",),
        angle_center=250.0,   # up-left; gap between FV (max 177°) and SHZH (min 262°)
        angle_tolerance=20.0,
        expect_curve=False,   # short straight flick
        aspect_hint="balanced",
        description="Short straight up-left flick (H = /h/)",
    ),
}

# Ordered list for deterministic iteration (dict is insertion-ordered in 3.7+)
ALL_FAMILIES: list[str] = list(FAMILY_DEFINITIONS.keys())

# Minimum raw score to produce a named classification instead of UNKNOWN
CONFIDENCE_THRESHOLD = 0.20

# Minimum score for a family to appear in the alternatives list
ALTERNATIVE_THRESHOLD = 0.10
