"""Core algorithm: turn every pixel close to a target color transparent.

Distance between a pixel and the target color is plain Euclidean distance in
RGB space, normalized to a 0-100 scale (0 = identical color, 100 = the
farthest possible color, e.g. black vs. white).

- Pixels within `tolerance` of the target color become fully transparent.
- Pixels between `tolerance` and `tolerance + feather` fade smoothly from
  transparent to their original alpha, instead of leaving a hard, jagged
  edge. This matters for AI-generated images, where a "solid" background
  color is usually anti-aliased against the subject.
- Pixels beyond `tolerance + feather` are left untouched.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image

RGB = tuple[int, int, int]

# Euclidean distance between the two farthest RGB colors (black, white).
_MAX_RGB_DISTANCE = math.sqrt(3 * 255**2)


def color_to_alpha(
    image: Image.Image,
    target_color: RGB,
    tolerance: float = 10.0,
    feather: float = 5.0,
) -> Image.Image:
    """Return a copy of `image` with pixels near `target_color` made transparent.

    Args:
        image: source image (any Pillow mode; converted to RGBA internally).
        target_color: the (r, g, b) color to key out, each channel 0-255.
        tolerance: percent (0-100) of max color distance treated as an exact
            match -> fully transparent.
        feather: extra percent (0-100) beyond `tolerance` over which alpha
            eases back in, softening the cutout edge. 0 = hard edge.

    Returns:
        A new RGBA image; `image` is not modified.
    """
    if not (0 <= tolerance <= 100):
        raise ValueError(f"tolerance must be within [0, 100], got {tolerance}")
    if feather < 0:
        raise ValueError(f"feather must be >= 0, got {feather}")

    arr = np.asarray(image.convert("RGBA"), dtype=np.float32)
    rgb = arr[..., :3]
    alpha = arr[..., 3]

    diff = rgb - np.asarray(target_color, dtype=np.float32)
    dist = np.sqrt(np.sum(diff * diff, axis=-1))

    hard_cut = tolerance / 100 * _MAX_RGB_DISTANCE
    soft_cut = (tolerance + feather) / 100 * _MAX_RGB_DISTANCE

    if soft_cut > hard_cut:
        keep_ratio = np.clip((dist - hard_cut) / (soft_cut - hard_cut), 0.0, 1.0)
    else:
        keep_ratio = (dist > hard_cut).astype(np.float32)

    out = arr.copy()
    out[..., 3] = alpha * keep_ratio
    return Image.fromarray(np.round(out).astype(np.uint8), mode="RGBA")


def color_to_alpha_gimp(image: Image.Image, target_color: RGB) -> Image.Image:
    """Remove a target color from `image`, the way GIMP's "Color to Alpha" does.

    Unlike `color_to_alpha`, this isn't a threshold: every pixel is treated
    as a blend of the target color and some "true" foreground color, and the
    minimum alpha/foreground-color combination that could reproduce the
    pixel is solved for per RGB channel. This removes color fringing from
    anti-aliased or semi-transparent edges (e.g. a soft-edged white glow on
    a white background) that a plain tolerance cutoff leaves behind, at the
    cost of being fully automatic: there's no tolerance/feather to tune.

    Args:
        image: source image (any Pillow mode; converted to RGBA internally).
        target_color: the (r, g, b) color to remove, each channel 0-255.

    Returns:
        A new RGBA image; `image` is not modified.
    """
    eps = 1e-6
    arr = np.asarray(image.convert("RGBA"), dtype=np.float64) / 255.0
    rgb = arr[..., :3]
    orig_alpha = arr[..., 3]
    key = np.asarray(target_color, dtype=np.float64) / 255.0

    # Per-channel alpha needed to explain this pixel as (key blended with
    # some in-[0,1] foreground color) at that alpha, one-sided each way.
    above = (rgb - key) / np.clip(1.0 - key, eps, None)
    below = (key - rgb) / np.clip(key, eps, None)
    channel_alpha = np.clip(np.where(rgb > key, above, np.where(rgb < key, below, 0.0)), 0.0, 1.0)

    alpha = np.max(channel_alpha, axis=-1)
    alpha_safe = np.where(alpha > eps, alpha, 1.0)  # avoid div-by-zero; result unused where alpha ~ 0

    new_rgb = np.clip((rgb - key) / alpha_safe[..., np.newaxis] + key, 0.0, 1.0)
    new_rgb = np.where(alpha[..., np.newaxis] > eps, new_rgb, key)

    out = np.empty_like(arr)
    out[..., :3] = new_rgb
    out[..., 3] = alpha * orig_alpha
    return Image.fromarray(np.round(np.clip(out * 255.0, 0, 255)).astype(np.uint8), mode="RGBA")


def sample_pixel_color(image: Image.Image, xy: tuple[int, int]) -> RGB:
    """Read the RGB color of a single pixel."""
    x, y = xy
    width, height = image.size
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(
            f"Coordinate ({x}, {y}) is outside the image bounds ({width}x{height})."
        )
    r, g, b, *_ = image.convert("RGBA").getpixel((x, y))
    return (r, g, b)


_CORNERS = {
    "top-left": lambda w, h: (0, 0),
    "top-right": lambda w, h: (w - 1, 0),
    "bottom-left": lambda w, h: (0, h - 1),
    "bottom-right": lambda w, h: (w - 1, h - 1),
}


def sample_corner_color(image: Image.Image, corner: str = "top-left") -> RGB:
    """Read the RGB color at one corner of the image (handy for solid AI backgrounds)."""
    if corner not in _CORNERS:
        raise ValueError(f"corner must be one of {sorted(_CORNERS)}, got '{corner}'")
    width, height = image.size
    xy = _CORNERS[corner](width, height)
    return sample_pixel_color(image, xy)
