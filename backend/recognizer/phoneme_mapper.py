from recognizer.phoneme_definitions import PITMAN_TO_IPA


def map_symbols_to_phonemes(
    symbols: list[str],
    vowel_inserts: list[dict] | None = None,
) -> list[str]:
    """
    Convert an ordered list of Pitman symbol labels into IPA phoneme strings.

    Unknown symbols (not in PITMAN_TO_IPA) are silently omitted — the outline
    layer already filters UNKNOWN strokes before they reach this function, so
    an unknown symbol here indicates a future symbol type not yet defined.

    vowel_inserts — optional list of dicts, each with:
        after_index (int): consonant index after which to inject the vowel.
                           Use -1 to insert before the first consonant.
        ipa         (str): vowel IPA string to inject (e.g. "/ɪ/").
    When None or empty the function behaves identically to the M14 version.
    """
    consonants = [PITMAN_TO_IPA[s] for s in symbols if s in PITMAN_TO_IPA]

    if not vowel_inserts:
        return consonants

    # Group insertions by target position
    inserts_after: dict[int, list[str]] = {}
    for ins in vowel_inserts:
        idx = int(ins.get("after_index", -1))
        inserts_after.setdefault(idx, []).append(str(ins["ipa"]))

    result: list[str] = []
    for ipa in inserts_after.get(-1, []):
        result.append(ipa)

    for i, phoneme in enumerate(consonants):
        result.append(phoneme)
        for ipa in inserts_after.get(i, []):
            result.append(ipa)

    return result
