from __future__ import annotations

from pathlib import Path

import click
from PIL import Image

from imgedit.color_utils import ParseError as ColorParseError
from imgedit.color_utils import parse_hex_color
from imgedit.core.crop import ANCHORS, autocrop, crop_box, crop_to_size
from imgedit.geometry_utils import ParseError as GeometryParseError
from imgedit.geometry_utils import parse_box, parse_size


def _default_output_path(input_path: Path) -> Path:
    suffix = input_path.suffix or ".png"
    return input_path.with_name(f"{input_path.stem}.crop{suffix}")


@click.command("crop")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output file path. Defaults to '<input>.crop<ext>' next to the input.",
)
@click.option(
    "--box",
    "box_str",
    metavar="LEFT,TOP,RIGHT,BOTTOM",
    help="Crop to an explicit pixel box.",
)
@click.option(
    "--size",
    "size_str",
    metavar="WxH",
    help="Crop to this size, positioned within the image by --anchor.",
)
@click.option(
    "--anchor",
    type=click.Choice(sorted(ANCHORS)),
    default="center",
    show_default=True,
    help="Where to position --size within the source image.",
)
@click.option(
    "--auto",
    "auto_trim",
    is_flag=True,
    help="Auto-trim a uniform border around the subject.",
)
@click.option(
    "--bg-color",
    "bg_color_hex",
    metavar="HEX",
    help="Background color for --auto. Default: transparent pixels, or the top-left corner color.",
)
@click.option(
    "--tolerance",
    type=click.FloatRange(min=0),
    default=2.0,
    show_default=True,
    help="Percent color distance treated as background, used with --auto.",
)
@click.option(
    "--padding",
    type=click.IntRange(min=0),
    default=0,
    show_default=True,
    help="Pixels of margin to keep around the auto-trimmed subject.",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Overwrite the output file if it already exists.",
)
def crop_command(
    input_path: Path,
    output_path: Path | None,
    box_str: str | None,
    size_str: str | None,
    anchor: str,
    auto_trim: bool,
    bg_color_hex: str | None,
    tolerance: float,
    padding: int,
    force: bool,
) -> None:
    """Crop an image: an explicit box, a sized+anchored crop, or auto-trim.

    \b
    Examples:
      imgedit crop art.png --box 10,10,500,500
      imgedit crop art.png --size 512x512 --anchor top
      imgedit crop art.png --auto --padding 8
      imgedit crop art.png --auto --bg-color "#ffffff" --tolerance 5
    """
    modes = [("--box", box_str), ("--size", size_str), ("--auto", auto_trim)]
    given = [name for name, value in modes if value]
    if not given:
        raise click.UsageError("Specify one of --box, --size, or --auto.")
    if len(given) > 1:
        raise click.UsageError(
            f"Options {', '.join(given)} are mutually exclusive; pass only one."
        )

    image = Image.open(input_path)

    try:
        if box_str:
            box = parse_box(box_str)
            result = crop_box(image, box)
            desc = f"box {box}"
        elif size_str:
            size = parse_size(size_str)
            result = crop_to_size(image, size, anchor=anchor)
            desc = f"size {size[0]}x{size[1]} anchor={anchor}"
        else:
            bg_color = parse_hex_color(bg_color_hex) if bg_color_hex else None
            result = autocrop(image, bg_color=bg_color, tolerance=tolerance, padding=padding)
            desc = f"auto-trim (tolerance={tolerance}%, padding={padding})"
    except (ColorParseError, GeometryParseError, ValueError) as exc:
        raise click.UsageError(str(exc)) from exc

    out_path = output_path or _default_output_path(input_path)
    if out_path.exists() and not force:
        raise click.UsageError(f"'{out_path}' already exists. Pass -f/--force to overwrite.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(out_path)

    click.echo(f"crop: {desc}")
    click.echo(f"size: {result.size[0]}x{result.size[1]}")
    click.echo(f"saved: {out_path}")
