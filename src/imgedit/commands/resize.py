from __future__ import annotations

from pathlib import Path

import click
from PIL import Image

from imgedit.core.resize import RESAMPLE_FILTERS, resize_image


def _default_output_path(input_path: Path) -> Path:
    suffix = input_path.suffix or ".png"
    return input_path.with_name(f"{input_path.stem}.resize{suffix}")


@click.command("resize")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output file path. Defaults to '<input>.resize<ext>' next to the input.",
)
@click.option("--width", type=click.IntRange(min=1), help="Target width in pixels.")
@click.option("--height", type=click.IntRange(min=1), help="Target height in pixels.")
@click.option(
    "--scale",
    type=click.FloatRange(min=0, min_open=True),
    help="Scale factor, e.g. 0.5 for half size. Mutually exclusive with width/height/max-side.",
)
@click.option(
    "--max-side",
    type=click.IntRange(min=1),
    help="Fit within this many pixels on the longer side, keeping aspect ratio.",
)
@click.option(
    "--stretch",
    is_flag=True,
    help="With both --width and --height, stretch instead of preserving aspect ratio.",
)
@click.option(
    "--filter",
    "filter_name",
    type=click.Choice(sorted(RESAMPLE_FILTERS)),
    default="lanczos",
    show_default=True,
    help="Resampling filter.",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Overwrite the output file if it already exists.",
)
def resize_command(
    input_path: Path,
    output_path: Path | None,
    width: int | None,
    height: int | None,
    scale: float | None,
    max_side: int | None,
    stretch: bool,
    filter_name: str,
    force: bool,
) -> None:
    """Resize an image by width/height, a scale factor, or a max side length.

    \b
    Examples:
      imgedit resize art.png --width 512
      imgedit resize art.png --height 512
      imgedit resize art.png --scale 0.5
      imgedit resize art.png --max-side 1024
      imgedit resize art.png --width 512 --height 512 --stretch
    """
    groups = [
        ("--width/--height", width is not None or height is not None),
        ("--scale", scale is not None),
        ("--max-side", max_side is not None),
    ]
    given = [name for name, present in groups if present]
    if not given:
        raise click.UsageError("Specify one of --width/--height, --scale, or --max-side.")
    if len(given) > 1:
        raise click.UsageError(
            f"Options {', '.join(given)} are mutually exclusive; pass only one group."
        )
    if stretch and not (width and height):
        raise click.UsageError("--stretch requires both --width and --height.")

    image = Image.open(input_path)

    try:
        result = resize_image(
            image,
            width=width,
            height=height,
            scale=scale,
            max_side=max_side,
            keep_aspect=not stretch,
            resample=RESAMPLE_FILTERS[filter_name],
        )
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc

    out_path = output_path or _default_output_path(input_path)
    if out_path.exists() and not force:
        raise click.UsageError(f"'{out_path}' already exists. Pass -f/--force to overwrite.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(out_path)

    src_w, src_h = image.size
    click.echo(f"size: {src_w}x{src_h} -> {result.size[0]}x{result.size[1]}")
    click.echo(f"filter: {filter_name}")
    click.echo(f"saved: {out_path}")
