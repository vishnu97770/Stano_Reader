from recognizer.phoneme_definitions import PITMAN_TO_IPA


def map_symbols_to_phonemes(symbols: list[str]) -> list[str]:
    """
    Convert an ordered list of Pitman symbol labels into IPA phoneme strings.

    Unknown symbols (not in PITMAN_TO_IPA) are silently omitted — the outline
    layer already filters UNKNOWN strokes before they reach this function, so
    an unknown symbol here indicates a future symbol type not yet defined.
    """
    return [PITMAN_TO_IPA[s] for s in symbols if s in PITMAN_TO_IPA]
