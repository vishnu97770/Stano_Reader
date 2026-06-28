"""
Stroke extraction from preprocessed binary images.

Input: uint8 ndarray where strokes=255, background=0 (output of image_processor).
Output: list of ExtractedStroke dicts, each containing an ordered point sequence
        that matches the canvas stroke point format exactly:
        {"x": float, "y": float, "pressure": float, "timestamp": int}

Algorithm per connected component:
  1. Filter by area (too small = noise; too large = page border)
  2. Determine shape (elongated vs compact) from bounding box aspect ratio
  3. Elongated: tip-to-tip projection → sorted centerline → downsample
  4. Compact:   contour boundary → start at topmost point → downsample
"""

import math
import uuid
from dataclasses import dataclass, field

import cv2
import numpy as np

# ── Thresholds ────────────────────────────────────────────────────────────────

MIN_STROKE_AREA: int = 50        # px² in normalised image; below = noise
MAX_STROKE_AREA_RATIO: float = 0.30  # fraction of total image; above = border
MIN_STROKE_POINTS: int = 3       # discard extracted strokes shorter than this
TARGET_POINTS: int = 40          # target number of points per stroke


# ── Public types ──────────────────────────────────────────────────────────────

@dataclass
class ExtractedPoint:
    x: float
    y: float
    pressure: float = 0.5   # W3C default for mouse; no pressure info from image
    timestamp: int = 0

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "pressure": self.pressure, "timestamp": self.timestamp}


@dataclass
class ExtractedStroke:
    id: str
    points: list[ExtractedPoint] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"id": self.id, "points": [p.to_dict() for p in self.points]}


# ── Public entry point ────────────────────────────────────────────────────────

def extract_strokes(binary: np.ndarray) -> list[ExtractedStroke]:
    """
    Extract individual strokes from a preprocessed binary image.

    Args:
        binary: uint8 ndarray, strokes=255, background=0.

    Returns:
        List of ExtractedStroke objects in approximate left-to-right,
        top-to-bottom reading order.
    """
    if binary.size == 0:
        return []

    image_area = binary.shape[0] * binary.shape[1]
    max_area = int(image_area * MAX_STROKE_AREA_RATIO)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary, connectivity=8
    )

    strokes: list[ExtractedStroke] = []

    # Label 0 is the background; skip it
    for label in range(1, num_labels):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < MIN_STROKE_AREA or area > max_area:
            continue

        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        w = int(stats[label, cv2.CC_STAT_WIDTH])
        h = int(stats[label, cv2.CC_STAT_HEIGHT])

        # Crop component mask to bounding box for efficiency
        mask = (labels[y:y + h, x:x + w] == label).astype(np.uint8) * 255

        points = _extract_points(mask, offset_x=x, offset_y=y)
        if len(points) < MIN_STROKE_POINTS:
            continue

        strokes.append(ExtractedStroke(id=str(uuid.uuid4()), points=points))

    # Sort by centroid y then x (top-to-bottom, left-to-right reading order)
    strokes.sort(key=lambda s: (
        sum(p.y for p in s.points) / len(s.points),
        sum(p.x for p in s.points) / len(s.points),
    ))

    return strokes


# ── Point extraction strategies ───────────────────────────────────────────────

def _extract_points(
    mask: np.ndarray,
    offset_x: int = 0,
    offset_y: int = 0,
) -> list[ExtractedPoint]:
    """Choose elongated vs compact strategy based on bounding box shape."""
    h, w = mask.shape
    aspect = max(w, h) / max(1, min(w, h))

    if aspect >= 2.0:
        pts = _points_elongated(mask)
    else:
        pts = _points_compact(mask)

    # Apply bounding-box offset and build ExtractedPoint list
    result = []
    for i, (lx, ly) in enumerate(pts):
        result.append(ExtractedPoint(
            x=round(float(lx + offset_x), 2),
            y=round(float(ly + offset_y), 2),
            pressure=0.5,
            timestamp=i * 16,  # ~60 fps equivalent
        ))
    return result


def _points_elongated(mask: np.ndarray) -> list[tuple[float, float]]:
    """
    Centerline via tip-to-tip projection.

    1. Collect all foreground (x, y) pixel positions.
    2. Find tip1 = pixel farthest from centroid.
    3. Find tip2 = pixel farthest from tip1.
    4. Project all pixels onto tip1→tip2 direction and sort.
    5. Divide sorted list into TARGET_POINTS bins; use mean position per bin.
    """
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return []

    pts_xy = np.column_stack([xs, ys]).astype(float)  # (N, 2), each row = [x, y]

    centroid = pts_xy.mean(axis=0)
    tip1 = pts_xy[np.argmax(np.linalg.norm(pts_xy - centroid, axis=1))]
    dists_from_tip1 = np.linalg.norm(pts_xy - tip1, axis=1)
    tip2 = pts_xy[np.argmax(dists_from_tip1)]

    direction = tip2 - tip1
    length = float(np.linalg.norm(direction))
    if length < 1e-6:
        cx, cy = float(centroid[0]), float(centroid[1])
        return [(cx, cy), (cx, cy)]

    unit = direction / length
    projections = np.dot(pts_xy - tip1, unit)

    order = np.argsort(projections)
    sorted_xy = pts_xy[order]

    n = min(TARGET_POINTS, len(sorted_xy))
    indices = np.linspace(0, len(sorted_xy) - 1, n).astype(int)

    result: list[tuple[float, float]] = []
    bin_size = max(1, len(sorted_xy) // n)
    for idx in indices:
        lo = max(0, idx - bin_size // 2)
        hi = min(len(sorted_xy), idx + bin_size // 2 + 1)
        local = sorted_xy[lo:hi]
        mx, my = float(local[:, 0].mean()), float(local[:, 1].mean())
        result.append((round(mx, 2), round(my, 2)))

    return result


def _points_compact(mask: np.ndarray) -> list[tuple[float, float]]:
    """
    Boundary-based extraction for compact shapes (circles, hooks, dots).

    Uses the external contour, starting from the topmost pixel, and
    samples TARGET_POINTS evenly around the perimeter.
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return []

    contour = max(contours, key=cv2.contourArea)
    pts = contour.reshape(-1, 2)  # (N, 2) each row = [x, y]

    if len(pts) < 2:
        x, y = float(pts[0, 0]), float(pts[0, 1])
        return [(x, y)]

    # Start at topmost point (smallest y value)
    topmost = int(np.argmin(pts[:, 1]))
    pts = np.roll(pts, -topmost, axis=0)

    n = min(TARGET_POINTS, len(pts))
    indices = np.linspace(0, len(pts) - 1, n).astype(int)
    return [(round(float(pts[i, 0]), 2), round(float(pts[i, 1]), 2)) for i in indices]
