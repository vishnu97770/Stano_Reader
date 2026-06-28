"""
Pitman shorthand hook definitions — pure data, no logic.

This milestone implements four small hooks:
  INITIAL: L Hook (/l/), R Hook (/r/)
  FINAL:   N Hook (/n/), F/V Hook (/f/ or /v/)

Future milestones extend this file to add:
  size = "LARGE"  — large hooks (different phoneme clusters)
  compound = True — compound hooks (two phonemes)
  name = "SHUN_HOOK_FINAL" etc.

No logic in hook_rules.py or hook_detector.py needs to change when
new definitions are added here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HookDefinition:
    name: str        # e.g. "L_HOOK_INITIAL"
    hook_type: str   # "L" | "R" | "N" | "FV"
    position: str    # "INITIAL" | "FINAL"
    phoneme: str     # primary IPA phoneme
    description: str
    size: str        # "SMALL" | "LARGE" — all in this milestone are "SMALL"
    compound: bool   # False — True for future compound hooks


HOOK_DEFINITIONS: dict[str, HookDefinition] = {
    "L_HOOK_INITIAL": HookDefinition(
        name="L_HOOK_INITIAL",
        hook_type="L",
        position="INITIAL",
        phoneme="/l/",
        description="Initial L hook: adds /l/ before the consonant (play, blow, clean)",
        size="SMALL",
        compound=False,
    ),
    "R_HOOK_INITIAL": HookDefinition(
        name="R_HOOK_INITIAL",
        hook_type="R",
        position="INITIAL",
        phoneme="/r/",
        description="Initial R hook: adds /r/ before the consonant (price, bring, train)",
        size="SMALL",
        compound=False,
    ),
    "N_HOOK_FINAL": HookDefinition(
        name="N_HOOK_FINAL",
        hook_type="N",
        position="FINAL",
        phoneme="/n/",
        description="Final N hook: adds /n/ after the consonant (open, ribbon, button)",
        size="SMALL",
        compound=False,
    ),
    "FV_HOOK_FINAL": HookDefinition(
        name="FV_HOOK_FINAL",
        hook_type="FV",
        position="FINAL",
        phoneme="/f/",
        description="Final F/V hook: adds /f/ or /v/ after the consonant",
        size="SMALL",
        compound=False,
    ),
}

# Ordered list for deterministic iteration
ALL_HOOK_TYPES: list[str] = list(HOOK_DEFINITIONS.keys())
