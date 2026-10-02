# emerge

A small NetLogo-like agent-based modeling library, written (and used) in plain Python.

```python
import random
from emerge import Model, Turtle, run

class Wanderer(Turtle):
    def setup(self):
        self.color = "blue"

    def step(self):
        self.right(random.uniform(-30, 30))
        self.forward(0.5)

run(Model(breeds={Wanderer: 100}))
```

```sh
uv run examples/wander.py
```

`run` opens a window with **Setup**, **Go** (toggle), and **Step** buttons, a speed
slider, and a tick counter. Keyboard shortcuts: `s` = Setup, `g`/space = Go, `t` = Step.

## Turtles

Subclass `Turtle` and override:

- `setup()`: called once when the turtle is created (at the origin, with a random heading and color).
- `step()`: called once per tick.

Don't override `__init__`. Each turtle can reach the world through `self.model`
(e.g. `self.model.ticks`, or `self.model.stop()` to halt the run).

### Commands

- `forward(d)` / `fd`, `back(d)` / `bk`
- `right(deg)` / `rt`, `left(deg)` / `lt`
- `x`, `y`, `heading`, `color`, `size` attributes

Coordinates follow NetLogo: the origin is at the center, y points up, heading 0 is north,
and headings increase clockwise. The world wraps at its edges.

Colors are NetLogo's base color names (`"red"`, `"sky"`, `"lime"`, ... see `emerge.colors`)
or `(r, g, b)` tuples.

## Model

`Model(breeds={Wolf: 10, Sheep: 100})` creates that many of each turtle class on Setup,
then steps every turtle in random order each tick.

World settings are constructor arguments: `max_x`, `max_y` (the world spans
`-max_x..max_x` patches), `patch_size` (pixels), and `background`. For world-level
behavior, subclass `Model` and override `setup()` or `go()`, setting the same names as
class attributes.
