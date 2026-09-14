"""Small helpers for parsing color/coordinate values from CLI strings."""

from __future__ import annotations

import re

RGB = tuple[int, int, int]


class ParseError(ValueError):
    """Raised when a user-supplied CLI value can't be parsed."""


def parse_hex_color(value: str) -> RGB:
    """Parse a hex color string ('#RRGGBB', 'RRGGBB', '#RGB', 'RGB') into (r, g, b)."""
    s = value.strip().lstrip("#")
    if re.fullmatch(r"[0-9a-fA-F]{3}", s):
        s = "".join(ch * 2 for ch in s)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", s):
        raise ParseError(
            f"'{value}' is not a valid hex color. Expected formats: '#RRGGBB' or '#RGB'."
        )
    r, g, b = (int(s[i : i + 2], 16) for i in (0, 2, 4))
    return (r, g, b)


def parse_xy(value: str) -> tuple[int, int]:
    """Parse an 'X,Y' pixel-coordinate string into (x, y)."""
    parts = value.split(",")
    if len(parts) != 2:
        raise ParseError(f"'{value}' is not a valid coordinate. Expected format: 'X,Y'.")
    try:
        x, y = (int(p.strip()) for p in parts)
    except ValueError as exc:
        raise ParseError(f"'{value}' is not a valid coordinate. Expected format: 'X,Y'.") from exc
    if x < 0 or y < 0:
        raise ParseError(f"Coordinates must be non-negative, got '{value}'.")
    return (x, y)


def format_hex_color(color: RGB) -> str:
    r, g, b = color
    return f"#{r:02x}{g:02x}{b:02x}"
