"""
Pitman-to-IPA mapping derived from SYMBOL_DEFINITIONS.

This module is the single access point for phoneme data.  It does not
duplicate symbol definitions — it derives the lookup table from the
existing source of truth so the two can never drift apart.
"""

from recognizer.symbol_definitions import SYMBOL_DEFINITIONS

# symbol label → IPA string, e.g. "P" → "/p/", "CH" → "/tʃ/"
PITMAN_TO_IPA: dict[str, str] = {
    symbol: defn.phoneme
    for symbol, defn in SYMBOL_DEFINITIONS.items()
}
