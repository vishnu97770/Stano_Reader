"""
Pure pressure analysis functions.

All functions take lists of point dicts and return primitives or dicts.
No I/O, no Pydantic, no FastAPI — fully testable in isolation.

Points may or may not carry a 'pressure' key:
  - Stylus / touch:  pressure ∈ [0, 1] (real hardware data)
  - Mouse:           pressure = 0.5    (browser spec default when button pressed)
  - Old stored data: pressure absent   (pre-M7 strokes loaded from SQLite)

compute_pressure_stats() returns None when no point carries pressure data.
Callers treat None as "pressure unavailable" and fall back to frequency priors.

Future hardware (tilt, twist) will be added as separate compute_*() functions
in this module following the same pattern.
"""


def average_pressure(pressures: list[float]) -> float:
    """Mean pressure across a stroke's sampled points, rounded to 4 dp."""
    if not pressures:
        return 0.0
    return round(sum(pressures) / len(pressures), 4)


def max_pressure(pressures: list[float]) -> float:
    """Peak pressure observed during the stroke, rounded to 4 dp."""
    if not pressures:
        return 0.0
    return round(max(pressures), 4)


def pressure_variance(pressures: list[float]) -> float:
    """
    Population variance of pressure across the stroke.
    0 = constant pressure throughout (e.g. pure mouse input).
    Higher values = variable pressure (typical of natural stylus use).
    """
    if len(pressures) < 2:
        return 0.0
    avg = sum(pressures) / len(pressures)
    return round(sum((p - avg) ** 2 for p in pressures) / len(pressures), 4)


def compute_pressure_stats(points: list[dict]) -> dict | None:
    """
    Extract pressure statistics from a list of raw point dicts.

    Returns a dict with keys {avg_pressure, max_pressure, variance, sample_count}
    compatible with PressureStats schema, or None if no point carries 'pressure'.

    Design note:
        Points without a 'pressure' key are skipped rather than treated as 0.
        This preserves the distinction between "no data" (key absent) and
        "zero pressure" (key present with value 0), preventing old stored strokes
        from appearing as ultra-light rather than unknown.
    """
    pressures = [
        float(p["pressure"])
        for p in points
        if "pressure" in p and p["pressure"] is not None
    ]

    if not pressures:
        return None

    return {
        "avg_pressure": average_pressure(pressures),
        "max_pressure": max_pressure(pressures),
        "variance": pressure_variance(pressures),
        "sample_count": len(pressures),
    }
