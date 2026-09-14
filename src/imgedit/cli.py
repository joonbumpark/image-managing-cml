from __future__ import annotations

import click

from imgedit import __version__
from imgedit.commands.color_to_alpha import color_to_alpha_command


@click.group()
@click.version_option(__version__, prog_name="imgedit")
def main() -> None:
    """imgedit - command-line image editing toolbox.

    A growing set of scriptable, non-interactive image-editing subcommands,
    designed to be easy to call by hand or from an automated/AI workflow.
    """


main.add_command(color_to_alpha_command)


if __name__ == "__main__":
    main()
