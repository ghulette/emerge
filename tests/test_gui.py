import pygame
import pytest

from emerge import Model
from emerge.gui import App


@pytest.fixture
def app():
    m = Model(max_x=5, max_y=5)
    a = App(m, "test")
    m.do_setup()
    yield a
    a.window.destroy()


def button(app, name):
    return next(b for b in app.buttons if b.name == name)


def click(app, down, up=None):
    app.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=down, button=1))
    app.handle(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=up or down, button=1))


def test_go_toggles_running(app):
    go = button(app, "go").rect.center
    click(app, go)
    assert app.running
    click(app, go)
    assert not app.running


def test_click_cancelled_by_releasing_elsewhere(app):
    click(app, button(app, "go").rect.center, up=(0, 0))
    assert not app.running


def test_step_and_setup_buttons(app):
    click(app, button(app, "step").rect.center)
    click(app, button(app, "step").rect.center)
    assert app.model.ticks == 2
    click(app, button(app, "setup").rect.center)
    assert app.model.ticks == 0


def test_keyboard_shortcuts(app):
    app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    assert app.running
    app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_t))
    assert not app.running and app.model.ticks == 1


def test_slider_sets_speed(app):
    r = app.slider_rect
    click(app, (r.left, r.centery))
    assert app.speed == 0
    click(app, (r.right - 1, r.centery))
    assert app.speed > 0.99


def test_running_advances_and_model_stop_is_reported(app):
    class Stops(Model):
        def go(self):
            if self.ticks == 3:
                self.stop()

    app.model = Stops(max_x=5, max_y=5)
    app.model.do_setup()
    app.running = True
    app.speed = 1.0
    app.advance(1.0)
    assert app.model.ticks == 3
    assert not app.running and app.stopped_by_model
