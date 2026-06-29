"""
Pitman shorthand symbol definitions — pure data, no logic.

In Pitman shorthand, each consonant pair within a family (e.g. P/B, T/D)
is geometrically identical.  The ONLY distinguishing feature is pen pressure:
  - Light stroke  = unvoiced consonant (P, T, K, CH, F, TH, S, SH)
  - Heavy stroke  = voiced consonant   (B, D, G, J,  V, DH, Z, ZH)

Since we cannot capture pressure without a stylus pressure sensor, the
classifier uses English phoneme frequency as a weak default prior.
All decisions made without pressure data carry thickness_missing=True
and a capped confidence ceiling.

Adding future families (N/NG, M/W, L, R, vowels) requires only new entries
in SYMBOL_DEFINITIONS and FAMILY_SYMBOLS — no logic changes anywhere else.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolDefinition:
    symbol: str           # Pitman symbol label ("P", "CH", "TH", etc.)
    family: str           # Parent family ("PB_FAMILY", etc.)
    is_voiced: bool       # False = unvoiced (light), True = voiced (heavy)
    phoneme: str          # IPA approximation for reference
    description: str      # English description of the sound


SYMBOL_DEFINITIONS: dict[str, SymbolDefinition] = {
    # PB_FAMILY
    "P":  SymbolDefinition("P",  "PB_FAMILY",   False, "/p/",  "Unvoiced bilabial stop (pin)"),
    "B":  SymbolDefinition("B",  "PB_FAMILY",   True,  "/b/",  "Voiced bilabial stop (bin)"),

    # TD_FAMILY
    "T":  SymbolDefinition("T",  "TD_FAMILY",   False, "/t/",  "Unvoiced alveolar stop (tin)"),
    "D":  SymbolDefinition("D",  "TD_FAMILY",   True,  "/d/",  "Voiced alveolar stop (din)"),

    # KG_FAMILY
    "K":  SymbolDefinition("K",  "KG_FAMILY",   False, "/k/",  "Unvoiced velar stop (cap)"),
    "G":  SymbolDefinition("G",  "KG_FAMILY",   True,  "/ɡ/",  "Voiced velar stop (gap)"),

    # CHJ_FAMILY
    "CH": SymbolDefinition("CH", "CHJ_FAMILY",  False, "/tʃ/", "Unvoiced palatal affricate (chip)"),
    "J":  SymbolDefinition("J",  "CHJ_FAMILY",  True,  "/dʒ/", "Voiced palatal affricate (jar)"),

    # FV_FAMILY
    "F":  SymbolDefinition("F",  "FV_FAMILY",   False, "/f/",  "Unvoiced labiodental fricative (fan)"),
    "V":  SymbolDefinition("V",  "FV_FAMILY",   True,  "/v/",  "Voiced labiodental fricative (van)"),

    # THDH_FAMILY — DH listed first because /ð/ ("the") is the most frequent
    # English consonant phoneme; it outranks /θ/ as the default guess.
    "TH": SymbolDefinition("TH", "THDH_FAMILY", False, "/θ/",  "Unvoiced dental fricative (thin)"),
    "DH": SymbolDefinition("DH", "THDH_FAMILY", True,  "/ð/",  "Voiced dental fricative (the)"),

    # SZ_FAMILY — S strongly favoured by English frequency
    "S":  SymbolDefinition("S",  "SZ_FAMILY",   False, "/s/",  "Unvoiced sibilant (sip)"),
    "Z":  SymbolDefinition("Z",  "SZ_FAMILY",   True,  "/z/",  "Voiced sibilant (zip)"),

    # SHZH_FAMILY
    "SH": SymbolDefinition("SH", "SHZH_FAMILY", False, "/ʃ/",  "Unvoiced palatal fricative (she)"),
    "ZH": SymbolDefinition("ZH", "SHZH_FAMILY", True,  "/ʒ/",  "Voiced palatal fricative (measure)"),

    # ── M19: Nine new consonant symbols ─────────────────────────────────────────

    # MW_FAMILY — M large/long open curve, W small/short open curve
    "M":  SymbolDefinition("M",  "MW_FAMILY",   False, "/m/",  "Bilabial nasal (man)"),
    "W":  SymbolDefinition("W",  "MW_FAMILY",   False, "/w/",  "Bilabial approximant (win)"),

    # LR_FAMILY — L straight up-right, R curved up-right; is_voiced used for
    # the is_voiced field only (R treated as voiced proxy for curvature pairing)
    "L":  SymbolDefinition("L",  "LR_FAMILY",   False, "/l/",  "Alveolar lateral approximant (leg)"),
    "R":  SymbolDefinition("R",  "LR_FAMILY",   True,  "/r/",  "Alveolar rhotic approximant (red)"),

    # NN_FAMILY — N short curve (unvoiced proxy), NG long curve, NK with hook
    "N":  SymbolDefinition("N",  "NN_FAMILY",   False, "/n/",  "Alveolar nasal (net)"),
    "NG": SymbolDefinition("NG", "NN_FAMILY",   True,  "/ŋ/",  "Velar nasal (ring)"),
    "NK": SymbolDefinition("NK", "NN_FAMILY",   True,  "/ŋk/", "Velar nasal-stop cluster (think)"),

    # Y_FAMILY — single-member
    "Y":  SymbolDefinition("Y",  "Y_FAMILY",    False, "/j/",  "Palatal approximant (yes)"),

    # H_FAMILY — single-member
    "H":  SymbolDefinition("H",  "H_FAMILY",    False, "/h/",  "Glottal fricative (hat)"),
}

# Ordered symbol tuple per family.  Variable-length: most families have 2 members;
# NN_FAMILY has 3; Y_FAMILY and H_FAMILY have 1.
# Order matters for two-member families: index 0 is the higher-frequency prior.
# THDH is deliberately reversed (DH first) — /ð/ more frequent than /θ/.
FAMILY_SYMBOLS: dict[str, tuple[str, ...]] = {
    "PB_FAMILY":   ("P",  "B"),
    "TD_FAMILY":   ("T",  "D"),
    "KG_FAMILY":   ("K",  "G"),
    "CHJ_FAMILY":  ("CH", "J"),
    "FV_FAMILY":   ("F",  "V"),
    "THDH_FAMILY": ("DH", "TH"),   # DH first — /ð/ more frequent than /θ/
    "SZ_FAMILY":   ("S",  "Z"),
    "SHZH_FAMILY": ("SH", "ZH"),
    # M19 families
    "MW_FAMILY":   ("M",  "W"),
    "LR_FAMILY":   ("L",  "R"),
    "NN_FAMILY":   ("N",  "NG", "NK"),
    "Y_FAMILY":    ("Y",),
    "H_FAMILY":    ("H",),
}

# Maximum confidence achievable when thickness data is absent.
# Reflects honest uncertainty: we can only apply frequency priors, not geometry.
THICKNESS_MISSING_CONFIDENCE_CAP = 0.62

# Reason string embedded in SymbolResult when pressure data is unavailable.
THICKNESS_MISSING_REASON = (
    "Pen pressure unavailable — voiced/unvoiced distinction requires thickness data. "
    "Confidence reflects English phoneme frequency only."
)
