"""Core simulation objects: the Model (world) and its Turtles.

Coordinates follow NetLogo: the origin is the center of the world, x grows to
the right, y grows upward, and one unit is one patch. Headings are in degrees,
with 0 pointing north and angles increasing clockwise. The world wraps around
at its edges.
"""

import math
import random

from . import colors
from .colors import Color


class Turtle:
    """An agent. Subclass it and override `setup` and `step`.

    Don't override `__init__`; do per-turtle initialization in `setup`, which
    runs right after the model creates the turtle (with a random heading and
    color, at the origin).
    """

    def __init__(
        self,
        model: "Model",
        x: float = 0.0,
        y: float = 0.0,
        heading: float = 0.0,
        color: str | Color = "red",
        size: float = 1.0,
    ):
        self.model = model
        self.x = x
        self.y = y
        self.heading = heading
        self.color = color
        self.size = size

    # --- Override these -------------------------------------------------

    def setup(self) -> None:
        """Called once when the turtle is created."""

    def step(self) -> None:
        """Called once per tick."""

    # --- State ----------------------------------------------------------

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
    def color(self, value: str | Color) -> None:
        self._color = colors.to_rgb(value)

    def forward(self, distance: float) -> None:
        """Move `distance` patches in the direction of the current heading."""
        rad = math.radians(self._heading)
        self.x, self.y = self.model.wrap(
            self.x + distance * math.sin(rad),
            self.y + distance * math.cos(rad),
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

    def __repr__(self) -> str:
        return f"<{type(self).__name__} x={self.x:.2f} y={self.y:.2f} heading={self._heading:.1f}>"


class Model:
    """A simulation world and the turtles in it.

    `breeds` maps Turtle subclasses to how many of each to create on setup:

        Model(breeds={Wolf: 10, Sheep: 100})

    Settings can be constructor arguments or, in a subclass, class attributes.
    The world spans patches -max_x..max_x horizontally and -max_y..max_y
    vertically, each drawn `patch_size` pixels wide.

    Most models only need Turtle subclasses. Subclass Model and override
    `setup` or `go` for world-level behavior.
    """

    breeds: dict[type[Turtle], int] = {}
    max_x: int = 16
    max_y: int = 16
    patch_size: int = 13
    background: str | Color = "black"

    def __init__(
        self,
        breeds: dict[type[Turtle], int] | None = None,
        max_x: int | None = None,
        max_y: int | None = None,
        patch_size: int | None = None,
        background: str | Color | None = None,
    ):
        if breeds is not None:
            self.breeds = breeds
        if max_x is not None:
            self.max_x = max_x
        if max_y is not None:
            self.max_y = max_y
        if patch_size is not None:
            self.patch_size = patch_size
        if background is not None:
            self.background = background
        self.turtles: list[Turtle] = []
        self.ticks = 0
        self._stopped = False

    # --- Override these -------------------------------------------------

    def setup(self) -> None:
        """Called on Setup, after the world is cleared. Creates the breeds."""
        for cls, n in self.breeds.items():
            self.create_turtles(n, cls)

    def go(self) -> None:
        """Called once per tick. Steps every turtle, in random order."""
        order = self.turtles[:]
        random.shuffle(order)
        for t in order:
            t.step()

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

    def random_x(self) -> float:
        return random.uniform(-self.max_x - 0.5, self.max_x + 0.5)

    def random_y(self) -> float:
        return random.uniform(-self.max_y - 0.5, self.max_y + 0.5)

    def clear(self) -> None:
        self.turtles.clear()
        self.ticks = 0
        self._stopped = False

    def create_turtles[T: Turtle](self, n: int, cls: type[T] = Turtle) -> list[T]:
        """Create `n` turtles of class `cls` at the origin, with random
        headings and colors, then call `setup` on each.
        """
        new = []
        for _ in range(n):
            t = cls(self, heading=random.uniform(0, 360), color=colors.random())
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
        self.setup()

    def step(self) -> bool:
        """Run one tick. Returns False if the model asked to stop."""
        self._stopped = False
        self.go()
        if self._stopped:
            return False
        self.ticks += 1
        return True
