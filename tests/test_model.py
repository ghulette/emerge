import math
import random

import pytest

from emerge import Model, Patch, Turtle


def turtle_at(model, x, y, heading=0.0):
    t = model.create_turtles(1)[0]
    t.x, t.y, t.heading = x, y, heading
    return t


# --- Turtle movement --------------------------------------------------------


def test_forward_follows_heading(model):
    t = turtle_at(model, 0, 0, heading=0)
    t.forward(1)
    assert (t.x, t.y) == pytest.approx((0, 1))
    t.right(90)
    t.forward(2)
    assert (t.x, t.y) == pytest.approx((2, 1))
    t.back(1)
    assert t.x == pytest.approx(1)


def test_turning_wraps_heading(model):
    t = turtle_at(model, 0, 0, heading=10)
    t.left(20)
    assert t.heading == pytest.approx(350)
    t.rt(370)
    assert t.heading == pytest.approx(0)


def test_forward_wraps_around_edges(model):
    # The world spans x in [-3.5, 3.5) and y in [-2.5, 2.5).
    t = turtle_at(model, 3.4, 0, heading=90)
    t.forward(0.2)
    assert t.x == pytest.approx(-3.4)
    t = turtle_at(model, 0, -2.4, heading=180)
    t.forward(0.2)
    assert t.y == pytest.approx(2.4)


def test_color_accepts_names(model):
    t = turtle_at(model, 0, 0)
    t.color = "sky"
    assert t.color == (45, 141, 190)


# --- Patches ----------------------------------------------------------------


def test_patch_grid(model):
    assert len(model.patches) == 7 * 5
    assert all(type(p) is Patch for p in model.patches)
    assert {(p.x, p.y) for p in model.patches} == {
        (x, y) for x in range(-3, 4) for y in range(-2, 3)
    }


def test_patch_at_rounds_to_nearest_center(model):
    p = model.patch_at(1.4, -0.6)
    assert (p.x, p.y) == (1, -1)
    assert model.patch_at(-3.5, -2.5) is model.patch_at(-3, -2)


def test_patch_at_wraps(model):
    assert model.patch_at(3.6, 0) is model.patch_at(-3, 0)
    assert model.patch_at(0, 2.5) is model.patch_at(0, -2)


def test_neighbors_wrap(model):
    corner = model.patch_at(3, 2)
    assert {(p.x, p.y) for p in corner.neighbors4} == {(3, -2), (-3, 2), (3, 1), (2, 2)}
    assert len(set(corner.neighbors)) == 8
    assert corner not in corner.neighbors


def test_turtle_and_patch_lookups(model):
    t = turtle_at(model, 0.2, -0.2, heading=90)
    assert t.patch is model.patch_at(0, 0)
    assert t.patch_ahead(1.2) is model.patch_at(1, 0)
    assert model.patch_at(0, 0).turtles == [t]
    t.move_to(model.patch_at(3, 2))
    assert (t.x, t.y) == (3, 2)
    assert model.patch_at(0, 0).turtles == []


# --- face / towards / distance ------------------------------------------------


@pytest.mark.parametrize(
    "target, heading",
    [((0, 2), 0), ((2, 0), 90), ((0, -2), 180), ((-2, 0), 270), ((1, 1), 45)],
)
def test_face_and_towards(model, target, heading):
    t = turtle_at(model, 0, 0, heading=123)
    other = turtle_at(model, *target)
    assert t.towards(other) == pytest.approx(heading)
    t.face(other)
    assert t.heading == pytest.approx(heading)


def test_face_patch(model):
    t = turtle_at(model, 0, 0)
    t.face(model.patch_at(-1, 0))
    assert t.heading == pytest.approx(270)


def test_distance(model):
    t = turtle_at(model, 0, 0)
    assert t.distance(turtle_at(model, 1.5, 2)) == pytest.approx(2.5)


def test_face_towards_distance_take_short_way_around(model):
    # Width is 7: from x=3 to x=-3 is 1 step east across the edge, not 6 west.
    t = turtle_at(model, 3, 0)
    other = turtle_at(model, -3, 0)
    assert t.distance(other) == pytest.approx(1)
    assert t.towards(other) == pytest.approx(90)


def test_face_same_spot_keeps_heading_and_towards_raises(model):
    t = turtle_at(model, 1, 1, heading=33)
    other = turtle_at(model, 1, 1)
    t.face(other)
    assert t.heading == 33
    with pytest.raises(ValueError):
        t.towards(other)


# --- Model lifecycle ----------------------------------------------------------


class Counter(Turtle):
    def setup(self):
        self.color = "lime"
        self.steps = 0

    def step(self):
        self.steps += 1


class Stopper(Turtle):
    def step(self):
        if self.model.ticks >= 4:
            self.model.stop()


def test_breeds_are_created_and_set_up():
    m = Model(breeds={Counter: 5, Stopper: 3})
    m.do_setup()
    assert sum(isinstance(t, Counter) for t in m.turtles) == 5
    assert sum(isinstance(t, Stopper) for t in m.turtles) == 3
    assert all(t.color == (44, 209, 59) for t in m.turtles if isinstance(t, Counter))


def test_step_advances_ticks_until_stopped():
    m = Model(breeds={Counter: 2, Stopper: 1})
    m.do_setup()
    while m.step():
        pass
    # Ticks 0-3 complete; tick 4 runs go() but stops, so isn't counted.
    assert m.ticks == 4
    assert all(t.steps == 5 for t in m.turtles if isinstance(t, Counter))


def test_setup_resets_world():
    m = Model(breeds={Counter: 2})
    m.do_setup()
    m.step()
    old_patch = m.patches[0]
    m.do_setup()
    assert m.ticks == 0
    assert len(m.turtles) == 2
    assert m.patches[0] is not old_patch


def test_patches_step_only_when_overridden():
    calls = []

    class Stepping(Patch):
        def step(self):
            calls.append(self)

    m = Model(patch_class=Stepping, max_x=2, max_y=2)
    m.do_setup()
    m.step()
    assert len(calls) == 25 and len(set(calls)) == 25


def test_patches_step_after_turtles():
    order = []

    class P(Patch):
        def step(self):
            order.append("patch")

    class T(Turtle):
        def step(self):
            order.append("turtle")

    m = Model(breeds={T: 2}, patch_class=P, max_x=0, max_y=0)
    m.do_setup()
    m.step()
    assert order == ["turtle", "turtle", "patch"]


def test_world_settings_as_class_attributes():
    class Big(Model):
        max_x = 5
        max_y = 1
        patch_size = 4

    m = Big()
    m.do_setup()
    assert (m.width, m.height, m.patch_size) == (11, 3, 4)
    assert len(m.patches) == 33
    assert math.isclose(m.wrap(5.6, 0)[0], -5.4)


# --- die / hatch ------------------------------------------------------------


def test_die_removes_turtle_from_model_and_patch(model):
    t = turtle_at(model, 1, 1)
    t.die()
    assert t not in model.turtles
    assert not t.alive
    assert model.patch_at(1, 1).turtles == []
    t.die()  # dying twice is harmless


def test_turtle_killed_mid_tick_is_not_stepped():
    stepped = []

    class Hunter(Turtle):
        def step(self):
            stepped.append(self)
            for other in self.model.turtles[:]:
                if other is not self:
                    other.die()

    m = Model(breeds={Hunter: 5}, max_x=2, max_y=2)
    m.do_setup()
    m.step()
    assert len(stepped) == 1 and len(m.turtles) == 1


def test_hatch_copies_parent_and_joins_next_tick():
    class Parent(Turtle):
        def setup(self):
            self.energy = 10
            self.steps = 0

        def step(self):
            self.steps += 1

    m = Model(breeds={Parent: 1}, max_x=3, max_y=3)
    m.do_setup()
    parent = m.turtles[0]
    assert isinstance(parent, Parent)
    parent.x, parent.y, parent.heading, parent.color = 1.2, -0.8, 45, "pink"
    children = parent.hatch(2)
    assert len(children) == 2 and len(m.turtles) == 3
    for child in children:
        assert type(child) is Parent and child is not parent
        assert (child.x, child.y, child.heading, child.color, child.energy) == (1.2, -0.8, 45, parent.color, 10)
        assert child in m.patch_at(1, -1).turtles
    children[0].energy = 3
    assert parent.energy == 10


def test_hatch_from_dying_parent_gives_live_children(model):
    parent = turtle_at(model, 0, 0)
    parent.die()
    (child,) = parent.hatch()
    assert child.alive and child in model.turtles and child in model.patch_at(0, 0).turtles


def test_patch_index_stays_consistent():
    random_ = random.Random(7)

    class Busy(Turtle):
        def step(self):
            self.right(random_.uniform(-90, 90))
            self.forward(random_.uniform(0, 2))
            roll = random_.random()
            if roll < 0.05:
                self.die()
            elif roll < 0.1:
                self.hatch()
            elif roll < 0.15:
                self.x += 3.3
            elif roll < 0.2:
                self.move_to(random_.choice(self.model.patches))

    m = Model(breeds={Busy: 40}, max_x=4, max_y=3)
    m.do_setup()
    for _ in range(100):
        m.step()
    for p in m.patches:
        assert set(p.turtles) == {t for t in m.turtles if m.patch_at(t.x, t.y) is p}
    assert sum(len(p.turtles) for p in m.patches) == len(m.turtles)
