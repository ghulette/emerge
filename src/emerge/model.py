"""Core simulation objects: the Model (world) and its Turtles.

Coordinates follow NetLogo: the origin is the center of the world, x grows to
the right, y grows upward, and one unit is one patch. Headings are in degrees,
with 0 pointing north and angles increasing clockwise. The world wraps around
at its edges.
"""

import copy
import math
import random
from collections.abc import Callable, Mapping
from typing import Any, Self, cast

from . import colors
from .colors import Color, ColorLike

# A metric's value: a number, or several named numbers charted together.
type MetricValue = float | Mapping[str, float]


class Turtle[P: Patch = Patch]:
    """An agent. Subclass it and override `setup` and `step`.

    To use your own Patch subclass's attributes through `self.patch` with
    type checking, parameterize the class: `class Cow(Turtle[Grass])`.

    Don't override `__init__`; do per-turtle initialization in `setup`, which
    runs right after the model creates the turtle (with a random heading and
    color, at the origin).

    By default a turtle is drawn as an arrow in its `color`. Set `shape` to an
    emoji to draw that instead (in its own colors). `shape_orient` controls how
    the emoji follows the turtle's heading:

    - None: never changes.
    - "rotate": rotates so its facing direction matches the heading.
    - "flip_x": mirrors left/right to face east or west (the default).
    - "flip_y": mirrors top/bottom to face north or south.
    - "flip_xy": both flips, e.g. for an emoji drawn facing diagonally.

    `shape_facing` is the heading the emoji is drawn facing: 270 (west) for
    most animal emoji, 45 for 🚀. These can be set per turtle or as class
    attributes.
    """

    shape: str | None = None
    shape_orient: str | None = "flip_x"
    shape_facing: float = 270.0

    def __init__(
        self,
        model: "Model[P]",
        x: float = 0.0,
        y: float = 0.0,
        heading: float = 0.0,
        color: ColorLike = "red",
        size: float = 1.0,
    ):
        self.model = model
        self._x = x
        self._y = y
        # The patch this turtle is indexed under (see Patch.turtles), or None
        # if it isn't in the world yet.
        self._patch: P | None = None
        self.heading = heading
        self.color = color
        self.size = size
        self.alive = True

    # --- Override these -------------------------------------------------

    def setup(self) -> None:
        """Called once when the turtle is created."""

    def step(self) -> None:
        """Called once per tick."""

    # --- State ----------------------------------------------------------

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float) -> None:
        self._set_position(value, self._y)

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float) -> None:
        self._set_position(self._x, value)

    def _set_position(self, x: float, y: float) -> None:
        self._x, self._y = x, y
        if self._patch is not None:
            patch = self.model.patch_at(x, y)
            if patch is not self._patch:
                del self._patch._turtles[self]
                patch._turtles[self] = None
                self._patch = patch

    def _enter_world(self) -> None:
        """Start tracking which patch this turtle is on."""
        self._patch = self.model.patch_at(self._x, self._y)
        self._patch._turtles[self] = None

    @property
    def heading(self) -> float:
        return self._heading

    @heading.setter
    def heading(self, value: float) -> None:
        self._heading = value % 360

    @property
    def color(self) -> Color:
        return self._color

    @color.setter
    def color(self, value: ColorLike) -> None:
        self._color = colors.to_rgb(value)

    def forward(self, distance: float) -> None:
        """Move `distance` patches in the direction of the current heading."""
        rad = math.radians(self._heading)
        self._set_position(
            *self.model.wrap(
                self._x + distance * math.sin(rad),
                self._y + distance * math.cos(rad),
            )
        )

    def back(self, distance: float) -> None:
        self.forward(-distance)

    def right(self, degrees: float) -> None:
        """Turn clockwise."""
        self.heading = self._heading + degrees

    def left(self, degrees: float) -> None:
        """Turn counterclockwise."""
        self.heading = self._heading - degrees

    # NetLogo-style abbreviations.
    fd = forward
    bk = back
    rt = right
    lt = left

    @property
    def patch(self) -> P:
        """The patch this turtle is standing on."""
        return self._patch or self.model.patch_at(self._x, self._y)

    def patch_ahead(self, distance: float) -> P:
        """The patch `distance` patches ahead along the current heading."""
        rad = math.radians(self._heading)
        return self.model.patch_at(
            self.x + distance * math.sin(rad),
            self.y + distance * math.cos(rad),
        )

    def move_to(self, target: "Turtle[Any] | Patch") -> None:
        """Jump to the location of a turtle or the center of a patch."""
        self._set_position(target.x, target.y)

    # --- Life and death ---------------------------------------------------

    def die(self) -> None:
        """Remove this turtle from the world. A turtle that dies during a
        tick isn't stepped for the rest of it.
        """
        if self.alive:
            self.alive = False
            self.model.turtles.remove(self)
            if self._patch is not None:
                del self._patch._turtles[self]
                self._patch = None

    def hatch[T: Turtle[Any]](self: T, n: int = 1) -> list[T]:
        """Create `n` copies of this turtle, like NetLogo's hatch: same class,
        position, heading, color, and other attributes (shallow-copied). They
        don't run `setup`, and start stepping next tick. Returns the new
        turtles so you can adjust them.
        """
        children = [copy.copy(self) for _ in range(n)]
        for child in children:
            child.alive = True
            child._enter_world()
        self.model.turtles.extend(children)
        return children

    def distance(self, target: "Turtle[Any] | Patch") -> float:
        """Distance to a turtle or patch center, the short way around the world."""
        dx, dy = self.model.offset(self.x, self.y, target.x, target.y)
        return math.hypot(dx, dy)

    def towards(self, target: "Turtle[Any] | Patch") -> float:
        """The heading that would point at a turtle or patch center, the short
        way around the world. Raises ValueError if the target is right here.
        """
        dx, dy = self.model.offset(self.x, self.y, target.x, target.y)
        if dx == 0 and dy == 0:
            raise ValueError(f"{self!r} is already at {target!r}; no heading towards it")
        return math.degrees(math.atan2(dx, dy)) % 360

    def face(self, target: "Turtle[Any] | Patch") -> None:
        """Turn to point at a turtle or patch center. Does nothing if the
        target is right here.
        """
        dx, dy = self.model.offset(self.x, self.y, target.x, target.y)
        if dx or dy:
            self.heading = math.degrees(math.atan2(dx, dy))

    def __repr__(self) -> str:
        return f"<{type(self).__name__} x={self.x:.2f} y={self.y:.2f} heading={self._heading:.1f}>"


class Patch:
    """One square of the world grid. Subclass it and override `setup` and
    `step` to give patches state and behavior.

    Patches have integer coordinates `x` and `y`, and a patch covers the
    points within half a unit of its center. Don't override `__init__`; do
    per-patch initialization in `setup`.

    Neighboring patches are typed as the same class, so a subclass's own
    attributes type-check on them.
    """

    def __init__(self, model: "Model[Any]", x: int, y: int):
        self.model: Model[Self] = model
        self.x = x
        self.y = y
        self.color = "black"
        # Turtles on this patch, kept up to date as they move. A dict, not a
        # set, so iteration order is deterministic.
        self._turtles: dict[Turtle[Any], None] = {}
        self._neighbors: list[Self] | None = None
        self._neighbors4: list[Self] | None = None

    # --- Override these -------------------------------------------------

    def setup(self) -> None:
        """Called once on Setup, before any turtles are created."""

    def step(self) -> None:
        """Called once per tick, after all turtles have stepped."""

    # --- State ----------------------------------------------------------

    @property
    def color(self) -> Color:
        return self._color

    @color.setter
    def color(self, value: ColorLike) -> None:
        self._color = colors.to_rgb(value)

    @property
    def neighbors(self) -> list[Self]:
        """The 8 surrounding patches."""
        if self._neighbors is None:
            self._neighbors = [
                self.model.patch_at(self.x + dx, self.y + dy)
                for dy in (1, 0, -1)
                for dx in (-1, 0, 1)
                if dx or dy
            ]
        return self._neighbors

    @property
    def neighbors4(self) -> list[Self]:
        """The 4 patches sharing an edge with this one (N, E, S, W)."""
        if self._neighbors4 is None:
            self._neighbors4 = [
                self.model.patch_at(self.x + dx, self.y + dy)
                for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))
            ]
        return self._neighbors4

    @property
    def turtles(self) -> list[Turtle[Any]]:
        """The turtles standing on this patch."""
        return list(self._turtles)

    def patch_at(self, dx: int, dy: int) -> Self:
        """The patch offset by (dx, dy) from this one."""
        return self.model.patch_at(self.x + dx, self.y + dy)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} x={self.x} y={self.y}>"


class Model[P: Patch = Patch]:
    """A simulation world and the turtles in it.

    `breeds` maps Turtle subclasses to how many of each to create on setup,
    and `patch_class` is the Patch subclass that fills the world:

        Model(breeds={Wolf: 10, Sheep: 100}, patch_class=Grass)

    Settings can be constructor arguments or, in a subclass, class attributes.
    The world spans patches -max_x..max_x horizontally and -max_y..max_y
    vertically, each drawn `patch_size` pixels wide.

    Most models only need Turtle and Patch subclasses. Subclass Model and
    override `setup` or `go` for world-level behavior.

    Metrics are numbers recorded after Setup and after every tick, into
    `history`, and charted live by the GUI. Pass `metrics`, a dict of names to
    functions of the model, or override the `metrics` method:

        Model(breeds={Cow: 30}, metrics={"cows": lambda m: len(m.turtles)})

    A metric can also return a dict of numbers, to chart several series
    together; each key becomes its own column in `history`:

        metrics={"population": lambda m: {"wolves": ..., "sheep": ...}}

    A Model subclass with its own Patch class can say so for type checking:
    `class Life(Model[Cell])`.
    """

    breeds: Mapping[type[Turtle[Any]], int] = {}
    patch_class: type[Patch] = Patch
    max_x: int = 16
    max_y: int = 16
    patch_size: int = 13

    def __init__(
        self,
        breeds: Mapping[type[Turtle[Any]], int] | None = None,
        patch_class: type[P] | None = None,
        max_x: int | None = None,
        max_y: int | None = None,
        patch_size: int | None = None,
        metrics: Mapping[str, Callable[[Self], MetricValue]] | None = None,
    ):
        if breeds is not None:
            self.breeds = breeds
        if max_x is not None:
            self.max_x = max_x
        if max_y is not None:
            self.max_y = max_y
        if patch_size is not None:
            self.patch_size = patch_size
        if patch_class is not None:
            self.patch_class = patch_class
        self.turtles: list[Turtle[P]] = []
        self.patches: list[P] = []
        self.ticks = 0
        self._stopped = False
        self._metric_fns: Mapping[str, Callable[[Self], MetricValue]] = metrics or {}
        self.history: dict[str, list[float | None]] = {"tick": []}
        # Chart name -> the history columns charted on it.
        self.metric_groups: dict[str, list[str]] = {}

    # --- Override these -------------------------------------------------

    def setup(self) -> None:
        """Called on Setup, after the world is reset to fresh patches and no
        turtles. Creates the breeds.
        """
        for cls, n in self.breeds.items():
            self.create_turtles(n, cls)

    def go(self) -> None:
        """Called once per tick. Steps every turtle, then every patch, each
        in random order.
        """
        order = self.turtles[:]
        random.shuffle(order)
        for t in order:
            if t.alive:
                t.step()
        # Stepping thousands of patches is slow, so skip it if it's a no-op.
        if self.patch_class.step is not Patch.step:
            order = self.patches[:]
            random.shuffle(order)
            for p in order:
                p.step()

    def metrics(self) -> Mapping[str, MetricValue]:
        """The values to record this tick, by name: numbers, or dicts of
        numbers to chart together. By default, evaluates the `metrics`
        functions passed to the constructor.
        """
        return {name: fn(self) for name, fn in self._metric_fns.items()}

    # --- World ----------------------------------------------------------

    @property
    def width(self) -> int:
        return 2 * self.max_x + 1

    @property
    def height(self) -> int:
        return 2 * self.max_y + 1

    def wrap(self, x: float, y: float) -> tuple[float, float]:
        """Wrap a point around the world's edges."""
        x = (x + self.max_x + 0.5) % self.width - self.max_x - 0.5
        y = (y + self.max_y + 0.5) % self.height - self.max_y - 0.5
        return x, y

    def offset(self, x1: float, y1: float, x2: float, y2: float) -> tuple[float, float]:
        """The (dx, dy) from point 1 to point 2, taking the shorter way around
        the world's edges.
        """
        dx = (x2 - x1 + self.width / 2) % self.width - self.width / 2
        dy = (y2 - y1 + self.height / 2) % self.height - self.height / 2
        return dx, dy

    def patch_at(self, x: float, y: float) -> P:
        """The patch containing the point (x, y), wrapping around the edges."""
        x, y = self.wrap(x, y)
        col = math.floor(x + 0.5) + self.max_x
        row = math.floor(y + 0.5) + self.max_y
        return self.patches[row * self.width + col]

    def random_x(self) -> float:
        return random.uniform(-self.max_x - 0.5, self.max_x + 0.5)

    def random_y(self) -> float:
        return random.uniform(-self.max_y - 0.5, self.max_y + 0.5)

    def clear(self) -> None:
        """Remove all turtles, replace every patch with a fresh one, and set
        up the new patches.
        """
        self.turtles.clear()
        self.patches = [
            cast(P, self.patch_class(self, x, y))
            for y in range(-self.max_y, self.max_y + 1)
            for x in range(-self.max_x, self.max_x + 1)
        ]
        for p in self.patches:
            p.setup()
        self.ticks = 0
        self._stopped = False

    def create_turtles[T: Turtle[Any]](self, n: int, cls: type[T] = Turtle) -> list[T]:
        """Create `n` turtles of class `cls` at the origin, with random
        headings and colors, then call `setup` on each.
        """
        new = []
        for _ in range(n):
            t = cls(self, heading=random.uniform(0, 360), color=colors.random())
            t._enter_world()
            t.setup()
            new.append(t)
        self.turtles.extend(new)
        return new

    # --- Running --------------------------------------------------------

    def stop(self) -> None:
        """Stop the Go loop (call from within `go`)."""
        self._stopped = True

    def do_setup(self) -> None:
        self.clear()
        self.history = {"tick": []}
        self.metric_groups = {}
        self.setup()
        self.record()

    def step(self) -> bool:
        """Run one tick. Returns False if the model asked to stop."""
        self._stopped = False
        self.go()
        if self._stopped:
            return False
        self.ticks += 1
        self.record()
        return True

    def simulate(self, ticks: int) -> dict[str, list[float | None]]:
        """Set up and run for up to `ticks` ticks without a window, stopping
        early if the model stops itself. Returns `history`.
        """
        self.do_setup()
        for _ in range(ticks):
            if not self.step():
                break
        return self.history

    @property
    def has_metrics(self) -> bool:
        return bool(self._metric_fns) or type(self).metrics is not Model.metrics

    def record(self) -> None:
        """Append the current tick and metrics to `history`. A metric missing
        from some ticks is recorded as None there, so every column in
        `history` stays the same length (e.g. for `pandas.DataFrame(history)`).
        """
        values: dict[str, float] = {}
        for name, value in self.metrics().items():
            series = value if isinstance(value, Mapping) else {name: value}
            group = self.metric_groups.setdefault(name, [])
            for column, v in series.items():
                if column not in group:
                    owner = next((g for g, cols in self.metric_groups.items() if column in cols), None)
                    if column == "tick" or owner is not None:
                        where = "is reserved" if column == "tick" else f"is already used by {owner!r}"
                        raise ValueError(f"metric series name {column!r} {where}")
                    group.append(column)
                values[column] = v
        n = len(self.history["tick"])
        for name in values:
            if name not in self.history:
                self.history[name] = [None] * n
        self.history["tick"].append(self.ticks)
        for name, column in self.history.items():
            if name != "tick":
                column.append(values.get(name))
