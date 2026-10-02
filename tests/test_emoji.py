import pytest

from emerge import Model, Turtle
from emerge.emoji import EmojiRenderer, orientation
from emerge.gui import App

WEST, NORTH, NORTHEAST = 270, 0, 45


@pytest.mark.parametrize("heading", [0, 90, 200, 333])
def test_none_never_changes(heading):
    assert orientation(None, heading, WEST) == (False, False, 0)


@pytest.mark.parametrize(
    "heading, flipped", [(0, False), (45, True), (90, True), (135, True), (180, False), (225, False), (270, False)]
)
def test_flip_x_faces_east_or_west(heading, flipped):
    assert orientation("flip_x", heading, WEST) == (flipped, False, 0)


@pytest.mark.parametrize(
    "heading, flipped", [(0, False), (90, False), (135, True), (180, True), (225, True), (315, False)]
)
def test_flip_y_faces_north_or_south(heading, flipped):
    assert orientation("flip_y", heading, NORTH) == (False, flipped, 0)


@pytest.mark.parametrize(
    "heading, flips", [(45, (False, False)), (135, (False, True)), (225, (True, True)), (315, (True, False))]
)
def test_flip_xy_picks_the_quadrant(heading, flips):
    assert orientation("flip_xy", heading, NORTHEAST) == (*flips, 0)


@pytest.mark.parametrize("heading, angle", [(270, 0), (0, 270), (90, 180), (180, 90), (271, 0)])
def test_rotate_turns_facing_to_heading(heading, angle):
    # pygame angles are counterclockwise; headings are clockwise.
    assert orientation("rotate", heading, WEST) == (False, False, angle)


def test_unknown_orient_raises():
    with pytest.raises(ValueError, match="shape_orient"):
        orientation("spin", 0, WEST)


@pytest.fixture
def renderer():
    r = EmojiRenderer()
    if r._load_font() is None:
        pytest.skip("no color emoji font on this system")
    return r


def test_renders_scaled_emoji(renderer):
    image = renderer.image("🐄", 40, "flip_x", 90, WEST)
    assert max(image.get_size()) == 40
    assert renderer.image("🐄", 40, "flip_x", 90, WEST) is image  # cached


def test_missing_glyph_returns_none(renderer):
    with pytest.warns(UserWarning, match="no glyph"):
        assert renderer.image("\U000f0000", 40, None, 0, WEST) is None


class Cow(Turtle):
    shape = "🐄"


def test_gui_draws_emoji_and_falls_back_to_arrows():
    m = Model(breeds={Cow: 3, Turtle: 2}, max_x=3, max_y=3)
    app = App(m, "emoji")
    m.do_setup()
    m.turtles[0].shape = "\U000f0000"  # no glyph: drawn as an arrow
    with pytest.warns(UserWarning):
        app.draw()
    app.window.destroy()
