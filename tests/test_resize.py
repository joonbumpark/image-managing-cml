from __future__ import annotations

import pytest
from PIL import Image

from imgedit.core.resize import resize_image


def _img(size=(100, 50)):
    return Image.new("RGB", size, (10, 20, 30))


class TestResizeImage:
    def test_width_only_keeps_aspect(self):
        out = resize_image(_img(), width=50)
        assert out.size == (50, 25)

    def test_height_only_keeps_aspect(self):
        out = resize_image(_img(), height=25)
        assert out.size == (50, 25)

    def test_width_and_height_keep_aspect_fits_inside(self):
        out = resize_image(_img(), width=40, height=40, keep_aspect=True)
        # aspect 100x50 -> fit within 40x40 -> 40x20
        assert out.size == (40, 20)

    def test_width_and_height_stretch(self):
        out = resize_image(_img(), width=40, height=40, keep_aspect=False)
        assert out.size == (40, 40)

    def test_scale(self):
        out = resize_image(_img(), scale=0.5)
        assert out.size == (50, 25)

    def test_max_side(self):
        out = resize_image(_img(size=(200, 100)), max_side=50)
        assert out.size == (50, 25)

    def test_max_side_portrait(self):
        out = resize_image(_img(size=(100, 200)), max_side=50)
        assert out.size == (25, 50)

    def test_no_args_raises(self):
        with pytest.raises(ValueError):
            resize_image(_img())

    def test_scale_with_width_raises(self):
        with pytest.raises(ValueError):
            resize_image(_img(), width=10, scale=0.5)

    def test_max_side_with_width_raises(self):
        with pytest.raises(ValueError):
            resize_image(_img(), width=10, max_side=50)

    def test_invalid_scale_raises(self):
        with pytest.raises(ValueError):
            resize_image(_img(), scale=0)

    def test_result_is_new_image(self):
        img = _img()
        out = resize_image(img, scale=1.0)
        assert out is not img
