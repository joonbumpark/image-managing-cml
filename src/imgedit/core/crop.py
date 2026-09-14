"""Core algorithms for cropping images."""

from __future__ import annotations

import math

import numpy as np
from PIL import Image

RGB = tuple[int, int, int]
Box = tuple[int, int, int, int]

# Euclidean distance between the two farthest RGB colors (black, white).
_MAX_RGB_DISTANCE = math.sqrt(3 * 255**2)

# Fraction along (width, height) that each anchor pins the crop box to.
ANCHORS = {
    "center": (0.5, 0.5),
    "top": (0.5, 0.0),
    "bottom": (0.5, 1.0),
    "left": (0.0, 0.5),
    "right": (1.0, 0.5),
    "top-left": (0.0, 0.0),
    "top-right": (1.0, 0.0),
    "bottom-left": (0.0, 1.0),
    "bottom-right": (1.0, 1.0),
}


def crop_box(image: Image.Image, box: Box) -> Image.Image:
    """Crop to an explicit (left, top, right, bottom) pixel box."""
    left, top, right, bottom = box
    width, height = image.size
    if right > width or bottom > height:
        raise ValueError(f"Box {box} extends beyond the image bounds ({width}x{height}).")
    return image.crop(box)


def crop_to_size(image: Image.Image, size: tuple[int, int], anchor: str = "center") -> Image.Image:
    """Crop to (width, height), positioned within the source image by `anchor`."""
    if anchor not in ANCHORS:
        raise ValueError(f"anchor must be one of {sorted(ANCHORS)}, got '{anchor}'")
    target_w, target_h = size
    src_w, src_h = image.size
    if target_w > src_w or target_h > src_h:
        raise ValueError(
            f"Crop size {target_w}x{target_h} is larger than the image ({src_w}x{src_h})."
        )
    anchor_x, anchor_y = ANCHORS[anchor]
    left = round((src_w - target_w) * anchor_x)
    top = round((src_h - target_h) * anchor_y)
    return image.crop((left, top, left + target_w, top + target_h))


def autocrop(
    image: Image.Image,
    bg_color: RGB | None = None,
    tolerance: float = 2.0,
    padding: int = 0,
) -> Image.Image:
    """Trim a uniform border around the subject.

    Background detection, in order of priority:
    - `bg_color` given: pixels within `tolerance` of it, or fully
      transparent, count as background.
    - `bg_color` omitted and the image already has transparent pixels:
      those pixels are the background (pure alpha-based trim).
    - Otherwise: the top-left corner's color is used as `bg_color`.
    """
    if tolerance < 0:
        raise ValueError(f"tolerance must be >= 0, got {tolerance}")
    if padding < 0:
        raise ValueError(f"padding must be >= 0, got {padding}")

    rgba = image.convert("RGBA")
    arr = np.asarray(rgba, dtype=np.float32)
    alpha = arr[..., 3]
    is_transparent = alpha <= 0

    if bg_color is not None:
        is_bg = is_transparent | _within_tolerance(arr, bg_color, tolerance)
    elif is_transparent.any():
        is_bg = is_transparent
    else:
        corner_color = tuple(int(v) for v in arr[0, 0, :3])
        is_bg = _within_tolerance(arr, corner_color, tolerance)

    is_fg = ~is_bg
    rows = np.any(is_fg, axis=1)
    cols = np.any(is_fg, axis=0)
    if not rows.any():
        raise ValueError("Nothing to crop: the whole image matches the background.")

    height, width = is_fg.shape
    top = int(np.argmax(rows))
    bottom = height - int(np.argmax(rows[::-1]))
    left = int(np.argmax(cols))
    right = width - int(np.argmax(cols[::-1]))

    if padding:
        left = max(0, left - padding)
        top = max(0, top - padding)
        right = min(width, right + padding)
        bottom = min(height, bottom + padding)

    return image.crop((left, top, right, bottom))


def _within_tolerance(rgba_arr: np.ndarray, color: RGB, tolerance: float) -> np.ndarray:
    diff = rgba_arr[..., :3] - np.asarray(color, dtype=np.float32)
    dist = np.sqrt(np.sum(diff * diff, axis=-1))
    return dist <= tolerance / 100 * _MAX_RGB_DISTANCE
