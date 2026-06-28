"""
Pitman writing position definitions — pure data, no detection logic.

Three positions exist relative to the writing line:
  FIRST  — stroke written above the line
  SECOND — stroke written through the line (most common)
  THIRD  — stroke written below the line

Baseline mode controls which reference lines are used:
  VIRTUAL    — equal-thirds of canvas height (current implementation)
  Future modes: PITMAN_RULED, SCANNED, CUSTOM
  Adding a new mode requires only a new constant and a branch in
  position_detector.py — position_definitions.py never changes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PositionDefinition:
    name: str          # "FIRST" | "SECOND" | "THIRD"
    label: str         # human-readable label
    description: str   # explanation for display / debugging


POSITION_DEFINITIONS: dict[str, PositionDefinition] = {
    "FIRST": PositionDefinition(
        name="FIRST",
        label="First Position",
        description="Stroke written above the writing line; baseline is below the stroke",
    ),
    "SECOND": PositionDefinition(
        name="SECOND",
        label="Second Position",
        description="Stroke written through the writing line; most common Pitman position",
    ),
    "THIRD": PositionDefinition(
        name="THIRD",
        label="Third Position",
        description="Stroke written below the writing line; baseline is above the stroke",
    ),
}

# Ordered list for deterministic band iteration
POSITION_ORDER: list[str] = ["FIRST", "SECOND", "THIRD"]

# Baseline mode identifiers — only VIRTUAL is implemented; others are reserved
BASELINE_MODE_VIRTUAL: str = "VIRTUAL"
SUPPORTED_BASELINE_MODES: frozenset[str] = frozenset({BASELINE_MODE_VIRTUAL})
