from __future__ import annotations

from pathlib import Path

import click
from PIL import Image

from imgedit.color_utils import ParseError, parse_hex_color
from imgedit.core.crop import autocrop


def _default_output_path(input_path: Path) -> Path:
    suffix = input_path.suffix or ".png"
    return input_path.with_name(f"{input_path.stem}.trim{suffix}")


@click.command("trim")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output file path. Defaults to '<input>.trim<ext>' next to the input.",
)
@click.option(
    "--bg-color",
    "bg_color_hex",
    metavar="HEX",
    help="Background color to trim. Default: transparent pixels, or the top-left corner color.",
)
@click.option(
    "--tolerance",
    type=click.FloatRange(min=0),
    default=2.0,
    show_default=True,
    help="Percent color distance still treated as background.",
)
@click.option(
    "--padding",
    type=click.IntRange(min=0),
    default=0,
    show_default=True,
    help="Pixels of margin to keep around the trimmed subject.",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Overwrite the output file if it already exists.",
)
def trim_command(
    input_path: Path,
    output_path: Path | None,
    bg_color_hex: str | None,
    tolerance: float,
    padding: int,
    force: bool,
) -> None:
    """Shrink the canvas to fit the actual content, trimming empty margins.

    E.g. a 512x512 image whose real content only fills the middle 300x300,
    with the rest transparent, becomes a tight 300x300 image.

    Background is transparent pixels by default. Pass --bg-color for an
    opaque background (e.g. a flat-colored canvas) instead.

    \b
    Examples:
      imgedit trim art.png
      imgedit trim art.png --padding 8
      imgedit trim art.png --bg-color "#ffffff" --tolerance 5
    """
    image = Image.open(input_path)

    try:
        bg_color = parse_hex_color(bg_color_hex) if bg_color_hex else None
        result = autocrop(image, bg_color=bg_color, tolerance=tolerance, padding=padding)
    except (ParseError, ValueError) as exc:
        raise click.UsageError(str(exc)) from exc

    out_path = output_path or _default_output_path(input_path)
    if out_path.exists() and not force:
        raise click.UsageError(f"'{out_path}' already exists. Pass -f/--force to overwrite.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(out_path)

    src_w, src_h = image.size
    click.echo(f"size: {src_w}x{src_h} -> {result.size[0]}x{result.size[1]}")
    click.echo(f"saved: {out_path}")
