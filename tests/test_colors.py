import pytest

from emerge import colors, scale_color

RED = colors.BASE_COLORS["red"]


def test_to_rgb_accepts_names_and_tuples():
    assert colors.to_rgb("red") == RED
    assert colors.to_rgb("RED") == RED
    assert colors.to_rgb("grey") == colors.to_rgb("gray")
    assert colors.to_rgb((1.9, 2, 3)) == (1, 2, 3)


def test_to_rgb_rejects_unknown_names():
    with pytest.raises(ValueError, match="unknown color"):
        colors.to_rgb("chartreuse-ish")


def test_random_is_a_base_color():
    assert colors.random() in colors.BASE_COLORS.values()


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, (0, 0, 0)),
        (5, RED),
        (10, (255, 255, 255)),
        (-3, (0, 0, 0)),
        (99, (255, 255, 255)),
    ],
)
def test_scale_color_runs_black_to_color_to_white(value, expected):
    assert scale_color("red", value, 0, 10) == expected


def test_scale_color_reversed_range():
    assert scale_color("red", 0, 10, 0) == (255, 255, 255)
    assert scale_color("red", 10, 10, 0) == (0, 0, 0)


def test_scale_color_interpolates():
    assert scale_color((100, 0, 200), 2.5, 0, 10) == (50, 0, 100)


def test_scale_color_empty_range_gives_base_color():
    assert scale_color("red", 7, 3, 3) == RED
