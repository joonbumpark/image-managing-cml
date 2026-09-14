from __future__ import annotations

from click.testing import CliRunner
from PIL import Image

from imgedit.cli import main


class TestTrimCLI:
    def test_transparent_margin_trimmed_to_content_size(self, tmp_path):
        # 512x512 canvas, real content is a 300x300 opaque square in the middle,
        # the rest transparent -> trimming should yield a tight 300x300 image.
        size = 512
        content = 300
        offset = (size - content) // 2

        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        for y in range(offset, offset + content):
            for x in range(offset, offset + content):
                img.putpixel((x, y), (200, 30, 30, 255))
        input_path = tmp_path / "art.png"
        img.save(input_path)

        result = CliRunner().invoke(main, ["trim", str(input_path)])

        assert result.exit_code == 0, result.output
        assert "512x512 -> 300x300" in result.output
        out_img = Image.open(tmp_path / "art.trim.png")
        assert out_img.size == (content, content)

    def test_default_output_path(self, tmp_path):
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        img.putpixel((5, 5), (9, 9, 9, 255))
        input_path = tmp_path / "art.png"
        img.save(input_path)

        result = CliRunner().invoke(main, ["trim", str(input_path)])

        assert result.exit_code == 0, result.output
        assert (tmp_path / "art.trim.png").exists()

    def test_padding_option(self, tmp_path):
        img = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
        for y in range(8, 12):
            for x in range(8, 12):
                img.putpixel((x, y), (9, 9, 9, 255))
        input_path = tmp_path / "art.png"
        img.save(input_path)

        result = CliRunner().invoke(main, ["trim", str(input_path), "--padding", "2"])

        assert result.exit_code == 0, result.output
        out_img = Image.open(tmp_path / "art.trim.png")
        assert out_img.size == (8, 8)  # 4x4 subject + 2px padding each side

    def test_solid_bg_color_trim(self, tmp_path):
        img = Image.new("RGB", (10, 10), (255, 255, 255))
        for y in range(3, 7):
            for x in range(3, 7):
                img.putpixel((x, y), (10, 10, 10))
        input_path = tmp_path / "art.png"
        img.save(input_path)

        result = CliRunner().invoke(
            main, ["trim", str(input_path), "--bg-color", "#ffffff", "--tolerance", "1"]
        )

        assert result.exit_code == 0, result.output
        out_img = Image.open(tmp_path / "art.trim.png")
        assert out_img.size == (4, 4)

    def test_all_background_reports_error(self, tmp_path):
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        input_path = tmp_path / "art.png"
        img.save(input_path)

        result = CliRunner().invoke(main, ["trim", str(input_path)])

        assert result.exit_code != 0
        assert "Nothing to crop" in result.output

    def test_refuses_to_overwrite_without_force(self, tmp_path):
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        img.putpixel((5, 5), (9, 9, 9, 255))
        input_path = tmp_path / "art.png"
        img.save(input_path)
        out_path = tmp_path / "art.trim.png"
        out_path.write_bytes(b"existing")

        result = CliRunner().invoke(main, ["trim", str(input_path)])

        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_force_overwrites(self, tmp_path):
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        img.putpixel((5, 5), (9, 9, 9, 255))
        input_path = tmp_path / "art.png"
        img.save(input_path)
        out_path = tmp_path / "art.trim.png"
        out_path.write_bytes(b"existing")

        result = CliRunner().invoke(main, ["trim", str(input_path), "-f"])

        assert result.exit_code == 0, result.output
