"""Small helpers for parsing box/size CLI strings."""

from __future__ import annotations

import re

Box = tuple[int, int, int, int]
Size = tuple[int, int]


class ParseError(ValueError):
    """Raised when a user-supplied CLI value can't be parsed."""


def parse_box(value: str) -> Box:
    """Parse 'LEFT,TOP,RIGHT,BOTTOM' into a 4-tuple of ints."""
    parts = value.split(",")
    if len(parts) != 4:
        raise ParseError(
            f"'{value}' is not a valid box. Expected format: 'LEFT,TOP,RIGHT,BOTTOM'."
        )
    try:
        left, top, right, bottom = (int(p.strip()) for p in parts)
    except ValueError as exc:
        raise ParseError(
            f"'{value}' is not a valid box. Expected format: 'LEFT,TOP,RIGHT,BOTTOM'."
        ) from exc
    if left < 0 or top < 0:
        raise ParseError(f"Box coordinates must be non-negative, got '{value}'.")
    if right <= left or bottom <= top:
        raise ParseError(f"Box must have RIGHT > LEFT and BOTTOM > TOP, got '{value}'.")
    return (left, top, right, bottom)


def parse_size(value: str) -> Size:
    """Parse 'WIDTHxHEIGHT' into a (width, height) tuple of ints."""
    match = re.fullmatch(r"\s*(\d+)\s*[xX]\s*(\d+)\s*", value)
    if not match:
        raise ParseError(f"'{value}' is not a valid size. Expected format: 'WIDTHxHEIGHT'.")
    width, height = int(match.group(1)), int(match.group(2))
    if width <= 0 or height <= 0:
        raise ParseError(f"Width and height must be positive, got '{value}'.")
    return (width, height)
