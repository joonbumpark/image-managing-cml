from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from imgedit.color_utils import ParseError, parse_hex_color, parse_xy
from imgedit.core.color_to_alpha import (
    color_to_alpha,
    color_to_alpha_gimp,
    sample_corner_color,
    sample_pixel_color,
)


def _solid(color, size=(8, 8), mode="RGB"):
    return Image.new(mode, size, color)


class TestParseHexColor:
    def test_six_digit(self):
        assert parse_hex_color("#ff0080") == (255, 0, 128)

    def test_three_digit(self):
        assert parse_hex_color("f08") == (255, 0, 136)

    def test_no_hash(self):
        assert parse_hex_color("000000") == (0, 0, 0)

    def test_invalid_raises(self):
        with pytest.raises(ParseError):
            parse_hex_color("not-a-color")


class TestParseXY:
    def test_basic(self):
        assert parse_xy("10,20") == (10, 20)

    def test_spaces(self):
        assert parse_xy(" 10 , 20 ") == (10, 20)

    def test_negative_rejected(self):
        with pytest.raises(ParseError):
            parse_xy("-1,2")

    def test_malformed_rejected(self):
        with pytest.raises(ParseError):
            parse_xy("10")


class TestColorToAlpha:
    def test_exact_match_becomes_transparent(self):
        img = _solid((255, 255, 255))
        out = color_to_alpha(img, (255, 255, 255), tolerance=1, feather=0)
        arr = np.asarray(out)
        assert (arr[..., 3] == 0).all()
        # RGB should be untouched
        assert (arr[..., :3] == 255).all()

    def test_far_color_untouched(self):
        img = _solid((0, 0, 0))
        out = color_to_alpha(img, (255, 255, 255), tolerance=10, feather=0)
        arr = np.asarray(out)
        assert (arr[..., 3] == 255).all()

    def test_feather_produces_partial_alpha(self):
        # A color at a known distance from white, inside the feather band.
        img = _solid((235, 235, 235))  # distance ~ sqrt(3*20^2) ~= 34.6
        out = color_to_alpha(img, (255, 255, 255), tolerance=5, feather=10)
        alpha = np.asarray(out)[0, 0, 3]
        assert 0 < alpha < 255

    def test_preserves_existing_alpha(self):
        img = Image.new("RGBA", (4, 4), (255, 255, 255, 128))
        out = color_to_alpha(img, (0, 0, 0), tolerance=5, feather=0)
        arr = np.asarray(out)
        # far from target color -> alpha preserved, not forced to 255
        assert (arr[..., 3] == 128).all()

    def test_invalid_tolerance_raises(self):
        img = _solid((0, 0, 0))
        with pytest.raises(ValueError):
            color_to_alpha(img, (0, 0, 0), tolerance=150)

    def test_output_is_rgba(self):
        img = _solid((1, 2, 3))
        out = color_to_alpha(img, (1, 2, 3))
        assert out.mode == "RGBA"


class TestColorToAlphaGimp:
    def test_exact_target_becomes_fully_transparent(self):
        img = _solid((10, 20, 30), mode="RGBA")
        out = color_to_alpha_gimp(img, (10, 20, 30))
        arr = np.asarray(out)
        assert (arr[..., 3] == 0).all()

    def test_far_color_stays_opaque_and_unchanged(self):
        img = _solid((0, 0, 0), mode="RGBA")
        out = color_to_alpha_gimp(img, (255, 255, 255))
        arr = np.asarray(out)
        assert (arr[..., 3] == 255).all()
        assert (arr[..., :3] == 0).all()

    def test_recovers_foreground_color_and_alpha(self):
        # A red foreground pixel blended 50/50 with a white key color:
        # observed = 0.5*red + 0.5*white = (255, 128, 128).
        img = Image.new("RGBA", (1, 1), (255, 128, 128, 255))
        out = color_to_alpha_gimp(img, (255, 255, 255))
        r, g, b, a = out.getpixel((0, 0))
        assert a == pytest.approx(128, abs=3)
        assert r == pytest.approx(255, abs=3)
        assert g == pytest.approx(0, abs=3)
        assert b == pytest.approx(0, abs=3)

    def test_preserves_existing_alpha(self):
        img = Image.new("RGBA", (2, 2), (0, 0, 0, 100))
        out = color_to_alpha_gimp(img, (255, 255, 255))
        arr = np.asarray(out)
        assert (arr[..., 3] == 100).all()

    def test_output_is_rgba(self):
        img = _solid((1, 2, 3))
        out = color_to_alpha_gimp(img, (1, 2, 3))
        assert out.mode == "RGBA"


class TestSampling:
    def test_sample_pixel_color(self):
        img = Image.new("RGB", (4, 4), (10, 20, 30))
        img.putpixel((1, 1), (40, 50, 60))
        assert sample_pixel_color(img, (1, 1)) == (40, 50, 60)
        assert sample_pixel_color(img, (0, 0)) == (10, 20, 30)

    def test_sample_pixel_out_of_bounds(self):
        img = Image.new("RGB", (4, 4), (0, 0, 0))
        with pytest.raises(ValueError):
            sample_pixel_color(img, (10, 10))

    def test_sample_corner_color(self):
        img = Image.new("RGB", (4, 4), (0, 0, 0))
        img.putpixel((3, 0), (9, 9, 9))
        assert sample_corner_color(img, "top-right") == (9, 9, 9)

    def test_sample_corner_invalid_name(self):
        img = Image.new("RGB", (4, 4), (0, 0, 0))
        with pytest.raises(ValueError):
            sample_corner_color(img, "middle")
