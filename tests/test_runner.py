import csv
import random

import pytest

from emerge import Model, Turtle, run
from emerge.gui import MAX_TICKS_PER_SECOND, App, slider_for


class Wanderer(Turtle):
    def step(self):
        self.right(random.uniform(-90, 90))
        self.forward(1)


def model():
    return Model(breeds={Wanderer: 10}, metrics={"x": lambda m: round(sum(t.x for t in m.turtles), 6)})


def test_headless_prints_final_metrics(capsys):
    m = model()
    run(m, args=["--headless", "--ticks", "7"])
    out = capsys.readouterr().out
    assert m.ticks == 7
    assert "ran 7 ticks" in out and "x:" in out


def test_seed_makes_runs_reproducible():
    a, b = model(), model()
    run(a, args=["--headless", "--ticks", "20", "--seed", "3"])
    run(b, args=["--headless", "--ticks", "20", "--seed", "3"])
    assert a.history == b.history


def test_csv_written(tmp_path):
    path = tmp_path / "out" / "run.csv"
    run(model(), args=["--headless", "--ticks", "3", "--csv", str(path)])
    rows = list(csv.reader(path.open()))
    assert rows[0] == ["tick", "x"]
    assert [r[0] for r in rows[1:]] == ["0", "1", "2", "3"]


@pytest.mark.parametrize("args", [["--headless"], ["--ticks", "-1"], ["--speed", "fast"], ["--bogus"]])
def test_bad_options_exit(args):
    with pytest.raises(SystemExit):
        run(model(), args=args)


def test_window_options_configure_app(monkeypatch):
    seen = {}

    def fake_run(self, go=False):
        seen.update(go=go, speed=self.steps_per_second(), stop_at=self.stop_at, title=self.title)
        self.window.destroy()

    monkeypatch.setattr(App, "run", fake_run)
    run(model(), args=["--go", "--speed", "100", "--ticks", "50"])
    assert seen["go"] is True
    assert seen["speed"] == pytest.approx(100)
    assert seen["stop_at"] == 50
    assert seen["title"] == "Wanderer"


def test_window_defaults(monkeypatch):
    seen = {}

    def fake_run(self, go=False):
        seen.update(go=go, stop_at=self.stop_at, speed=self.speed)
        self.window.destroy()

    monkeypatch.setattr(App, "run", fake_run)
    run(model(), args=[])
    assert seen == {"go": False, "stop_at": None, "speed": 0.5}


def test_slider_for_round_trips_and_clamps():
    assert slider_for(1) == 0
    assert slider_for(MAX_TICKS_PER_SECOND) == pytest.approx(1)
    assert slider_for(0.01) == 0
    assert slider_for(10_000) == 1
    assert MAX_TICKS_PER_SECOND ** slider_for(42) == pytest.approx(42)


def test_stop_at_stops_once_then_go_continues():
    m = model()
    app = App(m, "t")
    m.do_setup()
    app.stop_at = 3
    app.speed = 1.0
    app.running = True
    app.advance(1.0)
    assert m.ticks == 3 and not app.running and app.stopped_by_model
    app.press("go")
    app.advance(0.1)
    assert m.ticks > 3 and app.running
    app.window.destroy()

