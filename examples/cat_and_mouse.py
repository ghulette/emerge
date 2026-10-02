"""A mouse leaves a fading scent trail; cats track it down.

Patches show the scent with `scale_color`: no scent is black, fresh scent a
bright violet. Cats use `face` two ways: they turn toward the strongest-smelling
neighboring patch, and once they can see the mouse they face it directly. The
mouse faces the nearest cat and then turns around to flee.
"""

import random

from emerge import Model, Patch, Turtle, run, scale_color

SCENT_DECAY = 0.985
SIGHT = 6


class Ground(Patch):
    def setup(self):
        self.scent = 0.0

    def step(self):
        self.scent *= SCENT_DECAY
        # Top the range out above 1 so fresh scent is a light violet, not white.
        self.color = scale_color("violet", self.scent, 0, 1.3)


class Mouse(Turtle):
    shape = "🐁"

    def setup(self):
        self.size = 1.6

    def step(self):
        cats = [t for t in self.model.turtles if isinstance(t, Cat)]
        nearest = min(cats, key=self.distance)
        if self.distance(nearest) < SIGHT:
            self.face(nearest)
            self.right(180 + random.uniform(-45, 45))
        else:
            self.right(random.uniform(-30, 30))
        self.forward(0.5)
        self.patch.scent = 1.0


class Cat(Turtle):
    shape = "🐈"

    def setup(self):
        self.size = 2.4
        self.move_to(random.choice(self.model.patches))

    def step(self):
        mouse = next(t for t in self.model.turtles if isinstance(t, Mouse))
        if self.distance(mouse) < SIGHT:
            self.face(mouse)
        else:
            trail = max(self.patch.neighbors, key=lambda p: p.scent)
            if trail.scent > 0.01:
                self.face(trail)
            self.right(random.uniform(-20, 20))
        self.forward(0.35)


if __name__ == "__main__":
    run(Model(breeds={Mouse: 1, Cat: 3}, patch_class=Ground, max_x=30, max_y=20, patch_size=10))
