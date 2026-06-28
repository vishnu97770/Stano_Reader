"""
Image preprocessing pipeline for scanned / photographed Pitman shorthand.

All processing uses OpenCV and NumPy only — no AI, no neural networks.

Pipeline (in order):
  1. Decode bytes → BGR ndarray (supports JPEG, PNG, WEBP)
  2. Scale to fit within TARGET_WIDTH × TARGET_HEIGHT (preserves aspect ratio)
  3. Grayscale conversion
  4. Gaussian noise reduction (3×3 kernel)
  5. Adaptive thresholding → strokes=255, background=0
  6. Morphological close (fills gaps in strokes)
  7. Morphological open (removes isolated noise pixels)
  8. Deskew via projection-profile scoring on ±15° range

Output: uint8 ndarray, strokes=255, background=0, within TARGET dimensions.
"""

import math

import cv2
import numpy as np

TARGET_WIDTH: int = 800
TARGET_HEIGHT: int = 600

# Adaptive threshold block size must be odd
_ADAPT_BLOCK: int = 15
_ADAPT_C: int = 8          # constant subtracted from mean
_CLOSE_KERNEL: int = 3     # morphological close kernel size
_OPEN_KERNEL: int = 2      # morphological open kernel size

ACCEPTED_CONTENT_TYPES: frozenset[str] = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
})
MAX_FILE_BYTES: int = 10 * 1024 * 1024  # 10 MB


# ── Public entry point ────────────────────────────────────────────────────────

def preprocess_image(data: bytes) -> np.ndarray:
    """
    Accept raw image bytes (JPEG / PNG / WEBP) and return a binary ndarray
    ready for stroke extraction.

    Returns:
        uint8 ndarray with shape (H, W), values in {0, 255}.
        Strokes are white (255); background is black (0).
        H ≤ TARGET_HEIGHT and W ≤ TARGET_WIDTH.

    Raises:
        ValueError if the bytes cannot be decoded as an image.
    """
    bgr = _decode(data)
    bgr = _scale(bgr)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    binary = _adaptive_threshold(blurred)
    binary = _morphological_cleanup(binary)
    binary = _deskew(binary)
    return binary


def validate_upload(data: bytes, content_type: str) -> None:
    """
    Raise ValueError for files that are too large or have an unsupported type.
    Called by the API layer before preprocess_image.
    """
    if content_type not in ACCEPTED_CONTENT_TYPES:
        raise ValueError(
            f"Unsupported image format: {content_type!r}. "
            f"Accepted: {sorted(ACCEPTED_CONTENT_TYPES)}"
        )
    if len(data) > MAX_FILE_BYTES:
        mb = len(data) / (1024 * 1024)
        raise ValueError(f"File is {mb:.1f} MB; limit is 10 MB")


# ── Step implementations ──────────────────────────────────────────────────────

def _decode(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Could not decode image — unsupported or corrupt file")
    return bgr


def _scale(bgr: np.ndarray) -> np.ndarray:
    """Downscale to fit within TARGET dimensions; never upscale."""
    h, w = bgr.shape[:2]
    if w <= TARGET_WIDTH and h <= TARGET_HEIGHT:
        return bgr
    scale = min(TARGET_WIDTH / w, TARGET_HEIGHT / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)


def _adaptive_threshold(gray: np.ndarray) -> np.ndarray:
    """
    Convert grayscale to binary with ADAPTIVE_THRESH_GAUSSIAN_C.
    Uses THRESH_BINARY_INV so that ink strokes become white (255) and
    paper/background becomes black (0) — the convention used by
    connectedComponentsWithStats for foreground detection.
    """
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        _ADAPT_BLOCK,
        _ADAPT_C,
    )


def _morphological_cleanup(binary: np.ndarray) -> np.ndarray:
    # Close: bridge tiny gaps within strokes
    k_close = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (_CLOSE_KERNEL, _CLOSE_KERNEL)
    )
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, k_close)

    # Open: remove isolated noise pixels (smaller than 2×2)
    k_open = cv2.getStructuringElement(
        cv2.MORPH_RECT, (_OPEN_KERNEL, _OPEN_KERNEL)
    )
    return cv2.morphologyEx(closed, cv2.MORPH_OPEN, k_open)


def _deskew(binary: np.ndarray) -> np.ndarray:
    """
    Estimate skew angle in ±15° and rotate to correct it.

    Strategy: for each candidate angle, rotate the image and measure the
    variance of the horizontal projection profile.  Well-aligned text
    produces strongly striped rows → high variance.  The angle that
    maximises variance is the correction angle.
    """
    best_angle = 0
    best_score = -1.0

    for angle in range(-15, 16):
        rotated = _rotate(binary, float(angle))
        proj = np.sum(rotated, axis=1).astype(np.float32)
        score = float(np.var(proj))
        if score > best_score:
            best_score = score
            best_angle = angle

    if abs(best_angle) < 1:
        return binary
    return _rotate(binary, float(best_angle))


def _rotate(img: np.ndarray, angle: float) -> np.ndarray:
    h, w = img.shape[:2]
    cx, cy = w // 2, h // 2
    M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
    return cv2.warpAffine(
        img, M, (w, h),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
