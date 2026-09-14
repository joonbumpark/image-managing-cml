from __future__ import annotations

from pathlib import Path

import click
from PIL import Image

from imgedit.color_utils import ParseError, format_hex_color, parse_hex_color, parse_xy
from imgedit.core.color_to_alpha import color_to_alpha, sample_corner_color, sample_pixel_color


def _default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}.alpha.png")


@click.command("color-to-alpha")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output file path. Defaults to '<input>.alpha.png' next to the input.",
)
@click.option(
    "--color",
    "color_hex",
    metavar="HEX",
    help="Target color to make transparent, e.g. '#ffffff' or 'fff'.",
)
@click.option(
    "--pick",
    "pick_xy",
    metavar="X,Y",
    help="Sample the target color from a specific pixel instead of --color.",
)
@click.option(
    "--from-corner",
    "from_corner",
    type=click.Choice(["top-left", "top-right", "bottom-left", "bottom-right"]),
    help="Sample the target color from an image corner instead of --color.",
)
@click.option(
    "--tolerance",
    type=click.FloatRange(0, 100),
    default=10.0,
    show_default=True,
    help="Percent color distance treated as an exact match (-> fully transparent).",
)
@click.option(
    "--feather",
    type=click.FloatRange(min=0),
    default=5.0,
    show_default=True,
    help="Extra percent beyond --tolerance over which alpha fades in smoothly. Use 0 for a hard edge.",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Overwrite the output file if it already exists.",
)
def color_to_alpha_command(
    input_path: Path,
    output_path: Path | None,
    color_hex: str | None,
    pick_xy: str | None,
    from_corner: str | None,
    tolerance: float,
    feather: float,
    force: bool,
) -> None:
    """Make every pixel close to a specific color transparent (alpha = 0).

    Pick the target color one of three ways: --color HEX, --pick X,Y (sample
    a pixel), or --from-corner CORNER (sample a corner pixel). If none is
    given, defaults to sampling the top-left corner, which works well for
    typical AI-generated images with a solid-colored background.

    \b
    Examples:
      imgedit color-to-alpha art.png
      imgedit color-to-alpha art.png --color "#ffffff" --tolerance 15
      imgedit color-to-alpha art.png --pick 2,2 --tolerance 8 --feather 4
      imgedit color-to-alpha art.png --from-corner bottom-right -o out.png
    """
    selectors = [
        ("--color", color_hex),
        ("--pick", pick_xy),
        ("--from-corner", from_corner),
    ]
    given = [name for name, value in selectors if value]
    if len(given) > 1:
        raise click.UsageError(
            f"Options {', '.join(given)} are mutually exclusive; pass only one."
        )

    image = Image.open(input_path)

    try:
        if color_hex:
            target_color = parse_hex_color(color_hex)
            source_desc = f"--color {format_hex_color(target_color)}"
        elif pick_xy:
            xy = parse_xy(pick_xy)
            target_color = sample_pixel_color(image, xy)
            source_desc = f"pixel ({xy[0]}, {xy[1]}) = {format_hex_color(target_color)}"
        else:
            corner = from_corner or "top-left"
            target_color = sample_corner_color(image, corner)
            source_desc = f"{corner} corner = {format_hex_color(target_color)}"
    except (ParseError, ValueError) as exc:
        raise click.UsageError(str(exc)) from exc

    result = color_to_alpha(
        image,
        target_color=target_color,
        tolerance=tolerance,
        feather=feather,
    )

    out_path = output_path or _default_output_path(input_path)
    if out_path.exists() and not force:
        raise click.UsageError(f"'{out_path}' already exists. Pass -f/--force to overwrite.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(out_path)

    click.echo(f"target color: {source_desc}")
    click.echo(f"tolerance={tolerance}%  feather={feather}%")
    click.echo(f"saved: {out_path}")
