"""
Page layout analysis for scanned / photographed Pitman shorthand.

Input: preprocessed binary ndarray (strokes=255, background=0).
Output: PageMetadata describing writing zones and a canvas_height that is
        directly compatible with the position detector's canvas_height parameter.

Canvas height is always TARGET_HEIGHT (600) because the image is pre-scaled
to fit within that height in image_processor.py.  This means the position
detector normalises Y coordinates the same way it does for live canvas input.

Writing zone detection uses horizontal projection profiling:
  - Sum non-zero pixels in each row → projection array
  - Rows with density > threshold are inside a writing zone
  - Contiguous runs of such rows define individual writing lines
  - The bottom-most row of each zone is an estimate of its baseline
"""

from dataclasses import dataclass, field

import numpy as np

from recognizer.image_processor import TARGET_HEIGHT, TARGET_WIDTH


# ── Public types ──────────────────────────────────────────────────────────────

@dataclass
class WritingZone:
    top: float       # y-coordinate of first ink row in zone
    bottom: float    # y-coordinate of last ink row in zone
    baseline: float  # estimated baseline y (= bottom for Pitman strokes that sit ON the line)

    def to_dict(self) -> dict:
        return {"top": self.top, "bottom": self.bottom, "baseline": self.baseline}


@dataclass
class PageMetadata:
    canvas_width: float
    canvas_height: float       # always TARGET_HEIGHT; passed to detect_position
    writing_zones: list[WritingZone] = field(default_factory=list)
    line_count: int = 0
    image_width: int = 0       # actual pixel width of preprocessed image
    image_height: int = 0      # actual pixel height of preprocessed image

    def to_dict(self) -> dict:
        return {
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "writing_zones": [z.to_dict() for z in self.writing_zones],
            "line_count": self.line_count,
            "image_width": self.image_width,
            "image_height": self.image_height,
        }


# ── Tuning constants ──────────────────────────────────────────────────────────

# A row is "inked" if its total pixel sum ≥ this fraction of the row width
_INK_DENSITY_THRESHOLD: float = 0.02  # 2% of pixels in the row are ink
# Merge writing zones separated by fewer than this many blank rows
_MIN_GAP_ROWS: int = 5


# ── Public entry point ────────────────────────────────────────────────────────

def analyze_page(binary: np.ndarray) -> PageMetadata:
    """
    Analyse a preprocessed binary image and return page layout metadata.

    Args:
        binary: uint8 ndarray, strokes=255, background=0.

    Returns:
        PageMetadata with canvas_height=TARGET_HEIGHT and detected writing zones.
    """
    h, w = binary.shape[:2]

    if binary.size == 0 or h == 0 or w == 0:
        return PageMetadata(
            canvas_width=float(TARGET_WIDTH),
            canvas_height=float(TARGET_HEIGHT),
            writing_zones=[],
            line_count=0,
            image_width=w,
            image_height=h,
        )

    zones = _detect_writing_zones(binary, w)

    return PageMetadata(
        canvas_width=float(TARGET_WIDTH),
        canvas_height=float(TARGET_HEIGHT),
        writing_zones=zones,
        line_count=len(zones),
        image_width=w,
        image_height=h,
    )


# ── Zone detection ────────────────────────────────────────────────────────────

def _detect_writing_zones(binary: np.ndarray, width: int) -> list[WritingZone]:
    """
    Find contiguous horizontal bands that contain ink.

    Uses horizontal projection (row-wise pixel sum) to identify rows that
    contain strokes, then groups consecutive inked rows into zones.
    """
    h = binary.shape[0]
    # Row-wise sum → normalise by row width to get ink fraction per row
    projection = binary.sum(axis=1) / (255.0 * max(1, width))

    threshold = _INK_DENSITY_THRESHOLD

    inked = projection >= threshold  # bool array, True = row has ink

    zones: list[WritingZone] = []
    in_zone = False
    zone_start = 0
    gap_count = 0

    for row in range(h):
        if inked[row]:
            if not in_zone:
                in_zone = True
                zone_start = row
            gap_count = 0
        else:
            if in_zone:
                gap_count += 1
                if gap_count >= _MIN_GAP_ROWS:
                    zone_end = row - gap_count
                    zones.append(_make_zone(zone_start, zone_end))
                    in_zone = False
                    gap_count = 0

    if in_zone:
        zone_end = h - 1 - gap_count
        zones.append(_make_zone(zone_start, max(zone_start, zone_end)))

    return zones


def _make_zone(top: int, bottom: int) -> WritingZone:
    # Baseline = bottom of zone (Pitman strokes sit at or above the baseline)
    return WritingZone(
        top=float(top),
        bottom=float(bottom),
        baseline=float(bottom),
    )
