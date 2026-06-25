"""
Single entry point for stroke feature extraction.
Orchestrates calls to features.py and assembles a typed StrokeFeatures result.
"""

from recognizer.features import (
    compute_angle_and_direction,
    compute_bounding_box,
    compute_curve,
    compute_length,
)
from recognizer.pressure import compute_pressure_stats
from recognizer.schemas import BoundingBox, PressureStats, StrokeFeatures


def analyze_stroke(stroke_id: str, points: list[dict]) -> StrokeFeatures:
    """
    Extract geometric and pressure features from a raw stroke.

    Args:
        stroke_id: UUID of the stroke (echoed into the response).
        points:    List of dicts with keys {x, y, timestamp} and optional {pressure}.

    Returns:
        StrokeFeatures.  pressure_stats is None when no point carries pressure.

    Raises:
        ValueError: if points is empty.
    """
    if not points:
        raise ValueError(f"Cannot analyze stroke {stroke_id}: points list is empty")

    total_length, avg_segment = compute_length(points)
    direction, angle = compute_angle_and_direction(points)
    bbox = compute_bounding_box(points)
    is_curve, curvature_ratio = compute_curve(points)

    raw_pressure = compute_pressure_stats(points)
    pressure_stats = PressureStats(**raw_pressure) if raw_pressure else None

    return StrokeFeatures(
        stroke_id=stroke_id,
        length=round(total_length, 2),
        avg_segment_length=round(avg_segment, 2),
        direction=direction,
        angle=angle,
        bounding_box=BoundingBox(**bbox),
        point_count=len(points),
        avg_point_distance=round(avg_segment, 2),
        is_curve=is_curve,
        curvature_ratio=curvature_ratio,
        pressure_stats=pressure_stats,
    )
