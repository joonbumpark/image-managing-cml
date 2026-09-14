from __future__ import annotations

import pytest
from PIL import Image

from imgedit.core.crop import autocrop, crop_box, crop_to_size
from imgedit.geometry_utils import ParseError, parse_box, parse_size


class TestParseBox:
    def test_basic(self):
        assert parse_box("1,2,3,4") == (1, 2, 3, 4)

    def test_rejects_non_positive_extent(self):
        with pytest.raises(ParseError):
            parse_box("5,0,5,10")

    def test_rejects_negative(self):
        with pytest.raises(ParseError):
            parse_box("-1,0,5,10")

    def test_rejects_wrong_arity(self):
        with pytest.raises(ParseError):
            parse_box("1,2,3")


class TestParseSize:
    def test_basic(self):
        assert parse_size("100x200") == (100, 200)

    def test_case_insensitive(self):
        assert parse_size("100X200") == (100, 200)

    def test_rejects_invalid(self):
        with pytest.raises(ParseError):
            parse_size("100-200")

    def test_rejects_zero(self):
        with pytest.raises(ParseError):
            parse_size("0x200")


class TestCropBox:
    def test_basic(self):
        img = Image.new("RGB", (10, 10), (1, 2, 3))
        out = crop_box(img, (2, 2, 8, 6))
        assert out.size == (6, 4)

    def test_out_of_bounds_rejected(self):
        img = Image.new("RGB", (10, 10), (0, 0, 0))
        with pytest.raises(ValueError):
            crop_box(img, (0, 0, 20, 20))


class TestCropToSize:
    def test_center_anchor(self):
        img = Image.new("RGB", (10, 10), (0, 0, 0))
        img.putpixel((5, 5), (9, 9, 9))
        out = crop_to_size(img, (4, 4), anchor="center")
        assert out.size == (4, 4)
        # center pixel should be inside the crop
        assert out.getpixel((2, 2)) == (9, 9, 9)

    def test_top_left_anchor(self):
        img = Image.new("RGB", (10, 10), (0, 0, 0))
        img.putpixel((0, 0), (9, 9, 9))
        out = crop_to_size(img, (4, 4), anchor="top-left")
        assert out.getpixel((0, 0)) == (9, 9, 9)

    def test_too_large_rejected(self):
        img = Image.new("RGB", (10, 10), (0, 0, 0))
        with pytest.raises(ValueError):
            crop_to_size(img, (20, 20))

    def test_invalid_anchor_rejected(self):
        img = Image.new("RGB", (10, 10), (0, 0, 0))
        with pytest.raises(ValueError):
            crop_to_size(img, (4, 4), anchor="middle")


class TestAutocrop:
    def test_trims_transparent_border(self):
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        for y in range(3, 7):
            for x in range(3, 7):
                img.putpixel((x, y), (200, 30, 30, 255))
        out = autocrop(img)
        assert out.size == (4, 4)

    def test_trims_solid_bg_color(self):
        img = Image.new("RGB", (10, 10), (255, 255, 255))
        for y in range(3, 7):
            for x in range(3, 7):
                img.putpixel((x, y), (10, 10, 10))
        out = autocrop(img, bg_color=(255, 255, 255), tolerance=1)
        assert out.size == (4, 4)

    def test_defaults_to_corner_color(self):
        img = Image.new("RGB", (10, 10), (255, 255, 255))
        for y in range(2, 5):
            for x in range(2, 5):
                img.putpixel((x, y), (0, 0, 0))
        out = autocrop(img, tolerance=1)
        assert out.size == (3, 3)

    def test_padding_expands_and_clamps(self):
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        img.putpixel((5, 5), (9, 9, 9, 255))
        out = autocrop(img, padding=2)
        assert out.size == (5, 5)  # 3x3 (with clamped padding) around a 1x1 subject

    def test_all_background_raises(self):
        img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        with pytest.raises(ValueError):
            autocrop(img)
