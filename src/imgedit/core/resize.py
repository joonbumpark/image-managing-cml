"""Core algorithm for resizing images."""

from __future__ import annotations

from PIL import Image

RESAMPLE_FILTERS = {
    "nearest": Image.Resampling.NEAREST,
    "bilinear": Image.Resampling.BILINEAR,
    "bicubic": Image.Resampling.BICUBIC,
    "lanczos": Image.Resampling.LANCZOS,
}


def resize_image(
    image: Image.Image,
    width: int | None = None,
    height: int | None = None,
    scale: float | None = None,
    max_side: int | None = None,
    keep_aspect: bool = True,
    resample: int = Image.Resampling.LANCZOS,
) -> Image.Image:
    """Resize `image` by exactly one of: width/height, scale, or max_side.

    Args:
        width, height: target size in pixels. Either may be given alone (the
            other is derived from the aspect ratio); both together are
            treated as a bounding box (fit inside, preserving aspect) unless
            `keep_aspect` is False (stretch to exactly width x height).
        scale: multiply both dimensions by this factor.
        max_side: fit the image within a max_side x max_side box, preserving
            aspect ratio (i.e. resize so the longer side equals max_side).
        keep_aspect: when both width and height are given, preserve aspect
            ratio (fit within the box) instead of stretching.
        resample: a `PIL.Image.Resampling` filter.

    Returns:
        A new, resized image; `image` is not modified.
    """
    src_w, src_h = image.size

    if scale is not None:
        if width is not None or height is not None or max_side is not None:
            raise ValueError("--scale can't be combined with width/height/max_side.")
        if scale <= 0:
            raise ValueError(f"scale must be > 0, got {scale}")
        new_w = max(1, round(src_w * scale))
        new_h = max(1, round(src_h * scale))
    elif max_side is not None:
        if width is not None or height is not None:
            raise ValueError("--max-side can't be combined with width/height.")
        if max_side <= 0:
            raise ValueError(f"max_side must be > 0, got {max_side}")
        factor = max_side / max(src_w, src_h)
        new_w = max(1, round(src_w * factor))
        new_h = max(1, round(src_h * factor))
    elif width is not None and height is not None:
        if keep_aspect:
            factor = min(width / src_w, height / src_h)
            new_w = max(1, round(src_w * factor))
            new_h = max(1, round(src_h * factor))
        else:
            new_w, new_h = width, height
    elif width is not None:
        new_w = width
        new_h = max(1, round(src_h * (width / src_w)))
    elif height is not None:
        new_h = height
        new_w = max(1, round(src_w * (height / src_h)))
    else:
        raise ValueError("Specify one of: width/height, scale, or max_side.")

    return image.resize((new_w, new_h), resample=resample)
