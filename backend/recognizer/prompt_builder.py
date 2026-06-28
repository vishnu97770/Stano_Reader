"""
Prompt builder for AI-assisted candidate refinement.

Produces a structured natural-language prompt from recognition signals.
Pure function — no side effects, no I/O, fully testable in isolation.

Sections of every prompt (in order):
  1. Role anchor — establishes LLM expertise domain
  2. Domain context hint — legal / diplomatic / parliamentary / general
  3. Transcript context — last ≤10 accepted words (strongest next-word signal)
  4. Phoneme + vowel context — grounds the LLM in the acoustic signal
  5. Candidate list + output instruction — constrained to JSON only
"""

from __future__ import annotations

from recognizer.candidate_engine import CandidateResult

# ── Domain vocabulary hints ──────────────────────────────────────────────────

_DOMAIN_HINTS: dict[str, str] = {
    "legal": (
        "This shorthand is from a legal proceeding or document. "
        "Common terms include: motion, court, plaintiff, defendant, testimony, "
        "counsel, statute, deposition, affidavit, verdict, judge, jury, "
        "evidence, objection, ruling, brief, appeal, damages, contract, clause."
    ),
    "diplomatic": (
        "This shorthand is from a diplomatic correspondence or treaty. "
        "Common terms include: treaty, mandate, consul, delegation, protocol, "
        "attache, dispatch, envoy, ratify, plenipotentiary, communique, "
        "embassy, mission, accord, note, aide-memoire, convention, communique."
    ),
    "parliamentary": (
        "This shorthand is from a parliamentary debate or proceeding. "
        "Common terms include: motion, speaker, resolution, member, committee, "
        "division, adjournment, petition, amendment, clause, bill, reading, "
        "standing order, quorum, teller, debate, order, point, privilege."
    ),
    "general": "",
}

# ── Public entry point ────────────────────────────────────────────────────────


def build_prompt(
    candidates: list[CandidateResult],
    transcript_context: list[str],
    outline: str,
    ipa_sequence: list[str],
    vowel_signals: list[str],
    domain: str = "general",
) -> str:
    """
    Build a structured LLM prompt for candidate re-ranking.

    Args:
        candidates:         Ordered list from the deterministic engine.
        transcript_context: Last ≤10 accepted words (most recent last).
        outline:            Comma-separated recognised symbol names, e.g. "P, B, T".
        ipa_sequence:       IPA phoneme strings from the phoneme mapper.
        vowel_signals:      IPA strings of detected vowel marks, e.g. ["/æ/", "/iː/"].
        domain:             "general" | "legal" | "diplomatic" | "parliamentary".

    Returns:
        A UTF-8 string ready to send to a local LLM endpoint.
    """
    sections: list[str] = []

    # ── 1. Role ───────────────────────────────────────────────────────────────
    sections.append(
        "You are a Pitman shorthand expert helping to identify the most likely "
        "English word from a set of candidates produced by a deterministic "
        "recognition engine."
    )

    # ── 2. Domain context ─────────────────────────────────────────────────────
    domain_hint = _DOMAIN_HINTS.get(domain, "")
    if domain_hint:
        sections.append(f"Domain context: {domain_hint}")

    # ── 3. Transcript context ─────────────────────────────────────────────────
    recent = [w for w in transcript_context if w.strip()][-10:]
    if recent:
        joined = " ".join(recent)
        sections.append(
            f"The transcribed text so far ends with: \"{joined}\"\n"
            f"The next word should fit naturally after this context."
        )
    else:
        sections.append("No prior transcript context is available.")

    # ── 4. Phoneme + vowel context ────────────────────────────────────────────
    if ipa_sequence:
        phoneme_str = " ".join(ipa_sequence)
        sections.append(f"Consonant phoneme sequence detected: {phoneme_str}")
    if vowel_signals:
        vowel_str = ", ".join(vowel_signals)
        sections.append(f"Vowel signs detected: {vowel_str}")
    if outline:
        sections.append(f"Stroke outline symbols: {outline}")

    # ── 5. Candidates + instruction ───────────────────────────────────────────
    if candidates:
        cand_lines = "\n".join(
            f"  {i + 1}. {c.word}  (confidence {c.confidence:.2f})"
            for i, c in enumerate(candidates)
        )
        sections.append(
            f"Current candidate ranking:\n{cand_lines}\n\n"
            "Re-rank these candidates from most to least likely given all context above. "
            "Output ONLY a valid JSON array — no other text, no markdown, no code fence:\n"
            '[{"word": "<word>", "reason": "<one-sentence reason>"}, ...]'
        )
    else:
        sections.append(
            "No candidates are available. "
            "Output an empty JSON array: []"
        )

    return "\n\n".join(sections)
