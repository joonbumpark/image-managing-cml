from __future__ import annotations

from click.testing import CliRunner
from PIL import Image

from imgedit.cli import main


def _make_image(path, color=(255, 255, 255), size=(6, 6)):
    Image.new("RGB", size, color).save(path)


class TestColorToAlphaCLI:
    def test_default_corner_pick(self, tmp_path):
        input_path = tmp_path / "art.png"
        _make_image(input_path, color=(255, 255, 255))

        result = CliRunner().invoke(main, ["color-to-alpha", str(input_path)])

        assert result.exit_code == 0, result.output
        out_path = tmp_path / "art.alpha.png"
        assert out_path.exists()
        assert "top-left corner" in result.output

        out_img = Image.open(out_path)
        assert out_img.mode == "RGBA"
        assert out_img.getpixel((0, 0))[3] == 0

    def test_explicit_color_and_output(self, tmp_path):
        input_path = tmp_path / "art.png"
        _make_image(input_path, color=(0, 255, 0))
        out_path = tmp_path / "custom.png"

        result = CliRunner().invoke(
            main,
            [
                "color-to-alpha",
                str(input_path),
                "--color",
                "#00ff00",
                "-o",
                str(out_path),
            ],
        )

        assert result.exit_code == 0, result.output
        assert out_path.exists()

    def test_refuses_to_overwrite_without_force(self, tmp_path):
        input_path = tmp_path / "art.png"
        _make_image(input_path)
        out_path = tmp_path / "art.alpha.png"
        out_path.write_bytes(b"existing")

        result = CliRunner().invoke(main, ["color-to-alpha", str(input_path)])

        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_force_overwrites(self, tmp_path):
        input_path = tmp_path / "art.png"
        _make_image(input_path)
        out_path = tmp_path / "art.alpha.png"
        out_path.write_bytes(b"existing")

        result = CliRunner().invoke(main, ["color-to-alpha", str(input_path), "-f"])

        assert result.exit_code == 0, result.output

    def test_mutually_exclusive_selectors_rejected(self, tmp_path):
        input_path = tmp_path / "art.png"
        _make_image(input_path)

        result = CliRunner().invoke(
            main,
            ["color-to-alpha", str(input_path), "--color", "#fff", "--pick", "0,0"],
        )

        assert result.exit_code != 0
        assert "mutually exclusive" in result.output

    def test_invalid_color_reported(self, tmp_path):
        input_path = tmp_path / "art.png"
        _make_image(input_path)

        result = CliRunner().invoke(
            main, ["color-to-alpha", str(input_path), "--color", "not-a-color"]
        )

        assert result.exit_code != 0
        assert "not a valid hex color" in result.output
