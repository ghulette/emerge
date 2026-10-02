import pytest

from emerge import Model, Turtle
from emerge.charts import columns, format_value
from emerge.gui import App


class Walker(Turtle):
    def step(self):
        self.forward(1)


def test_no_metrics_records_only_ticks():
    m = Model(breeds={Walker: 2})
    assert not m.has_metrics
    m.simulate(3)
    assert m.history == {"tick": [0, 1, 2, 3]}


def test_metric_functions_recorded_after_setup_and_each_tick():
    m = Model(breeds={Walker: 2}, metrics={"turtles": lambda m: len(m.turtles), "tick²": lambda m: m.ticks**2})
    assert m.has_metrics
    history = m.simulate(3)
    assert history == {"tick": [0, 1, 2, 3], "turtles": [2, 2, 2, 2], "tick²": [0, 1, 4, 9]}


def test_overriding_metrics_method():
    class Counting(Model):
        def metrics(self):
            return {"double": self.ticks * 2}

    m = Counting()
    assert m.has_metrics
    assert m.simulate(2)["double"] == [0, 2, 4]


def test_missing_and_late_metrics_keep_columns_aligned():
    class Sometimes(Model):
        def metrics(self):
            if self.ticks == 0:
                return {"a": 1}
            return {"b": self.ticks}

    history = Sometimes().simulate(2)
    assert history == {"tick": [0, 1, 2], "a": [1, None, None], "b": [None, 1, 2]}


def test_simulate_stops_early_and_setup_resets_history():
    class Stops(Model):
        def go(self):
            if self.ticks == 2:
                self.stop()

    m = Stops(metrics={"t": lambda m: m.ticks})
    assert m.simulate(100) == {"tick": [0, 1, 2], "t": [0, 1, 2]}
    m.do_setup()
    assert m.history == {"tick": [0], "t": [0]}


def test_history_works_with_pandas_style_columns():
    history = Model(metrics={"x": lambda m: 1.5}).simulate(4)
    assert len({len(column) for column in history.values()}) == 1


@pytest.mark.parametrize(
    "value, text",
    [(None, "–"), (3, "3"), (3.0, "3"), (12345.6, "12,346"), (42.781, "42.78"), (0.00123, "0.00123")],
)
def test_format_value(value, text):
    assert format_value(value) == text


def test_columns_keep_short_series_and_bucket_long_ones():
    assert columns([0, 1, 2], [5, None, 7], 10) == [(0, 5, 5, 5), (2, 7, 7, 7)]
    cols = columns(list(range(100)), list(range(100)), 10)
    assert len(cols) == 10
    tick, mean, low, high = cols[0]
    assert (tick, mean, low, high) == (9, 4.5, 0, 9)


def test_gui_adds_chart_panel_only_with_metrics():
    plain = App(Model(max_x=5, max_y=5), "plain")
    assert plain.charts is None
    plain.window.destroy()

    m = Model(max_x=5, max_y=5, metrics={"a": lambda m: m.ticks, "b": lambda m: -m.ticks})
    app = App(m, "charts")
    assert app.charts is not None
    assert app.win_w > plain.win_w
    m.do_setup()
    app.draw()  # a single point
    for _ in range(500):
        m.step()
    app.draw()  # more ticks than pixels: bucketed
    app.window.destroy()
