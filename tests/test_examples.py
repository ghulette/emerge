"""Smoke tests: every example sets up, runs, and draws; Life follows its rules."""

import pytest

from emerge import Model
from emerge.gui import App

from conftest import load_example


def example_models():
    wander = load_example("wander")
    circles = load_example("circles")
    grazing = load_example("grazing")
    life = load_example("life")
    cat_and_mouse = load_example("cat_and_mouse")
    return {
        "wander": Model(breeds={wander.Wanderer: 20}),
        "circles": Model(breeds={circles.Circler: 10}),
        "grazing": Model(breeds={grazing.Cow: 5}, patch_class=grazing.Grass),
        "life": life.Life(max_x=10, max_y=10),
        "cat_and_mouse": Model(
            breeds={cat_and_mouse.Mouse: 1, cat_and_mouse.Cat: 3},
            patch_class=cat_and_mouse.Ground,
        ),
    }


@pytest.mark.parametrize("name", list(example_models()))
def test_example_runs_and_draws(name):
    model = example_models()[name]
    app = App(model, name)
    model.do_setup()
    for _ in range(20):
        model.step()
    app.draw()
    app.window.destroy()


@pytest.fixture
def life():
    module = load_example("life")
    m = module.Life(max_x=4, max_y=4)
    m.do_setup()
    for cell in m.patches:
        cell.set_alive(False)
    return m


def alive(m):
    return {(c.x, c.y) for c in m.patches if c.alive}


def set_cells(m, cells):
    for x, y in cells:
        m.patch_at(x, y).set_alive(True)


def test_life_blinker_oscillates(life):
    set_cells(life, [(-1, 0), (0, 0), (1, 0)])
    life.step()
    assert alive(life) == {(0, -1), (0, 0), (0, 1)}
    life.step()
    assert alive(life) == {(-1, 0), (0, 0), (1, 0)}


def test_life_still_life_stops_the_run(life):
    block = {(0, 0), (1, 0), (0, 1), (1, 1)}
    set_cells(life, block)
    assert life.step() is False
    assert alive(life) == block
