"""Particles orbit a central sun, slowly spiraling in.

Each particle keeps a velocity, accelerates toward the sun under inverse-square
gravity, and loses a little speed to drag every tick, so orbits gradually decay.
Particles whiten as they speed up and leave fading trails on the patches.
"""

import math
import random

from emerge import Model, Patch, Turtle, run, scale_color

GRAVITY = 5.0
SOFTENING = 1.5  # the pull fades smoothly to zero at the sun's center
DRAG = 0.9995  # fraction of velocity kept each tick
TRAIL_DECAY = 0.93
MIN_SUBSTEPS = 2
MAX_SUBSTEPS = 12


class Space(Patch):
    def setup(self):
        self.glow = 0.0
        self.color = "black"

    def step(self):
        if self.glow > 0.01:
            self.glow *= TRAIL_DECAY
            self.color = scale_color("sky", self.glow, 0, 2)
        elif self.glow:
            self.glow = 0.0
            self.color = "black"


class Sun(Turtle):
    shape = "☀️"
    shape_orient = None

    def setup(self):
        self.size = 3


class Particle(Turtle[Space]):
    def setup(self):
        self.size = 1.3
        self.move_to(random.choice(self.model.patches))
        self.x += random.uniform(-0.5, 0.5)
        self.y += random.uniform(-0.5, 0.5)
        # Start moving sideways around the center at roughly orbital speed,
        # with some randomness so orbits are elliptical.
        r = max(math.hypot(self.x, self.y), 1)
        speed = math.sqrt(GRAVITY / r) * random.uniform(0.6, 1.2)
        direction = random.choice((1, -1))
        self.vx = -self.y / r * speed * direction
        self.vy = self.x / r * speed * direction

    def step(self):
        sun = next(t for t in self.model.turtles if isinstance(t, Sun))
        # Integrate in sub-steps (more when moving fast) so close passes stay
        # accurate, and so fast particles leave unbroken trails.
        n = min(MAX_SUBSTEPS, max(MIN_SUBSTEPS, math.ceil(3 * math.hypot(self.vx, self.vy))))
        dt = 1 / n
        for _ in range(n):
            r = self.distance(sun)
            if r > 0:
                pull = GRAVITY * r / (r * r + SOFTENING * SOFTENING) ** 1.5
                angle = math.radians(self.towards(sun))
                self.vx += pull * math.sin(angle) * dt
                self.vy += pull * math.cos(angle) * dt
            speed = math.hypot(self.vx, self.vy)
            if speed > 0:
                self.heading = math.degrees(math.atan2(self.vx, self.vy))
                self.forward(speed * dt)
            self.patch.glow = 1.0
        self.vx *= DRAG
        self.vy *= DRAG
        # Yellow when slow, whitening as they speed up.
        self.color = scale_color("yellow", math.hypot(self.vx, self.vy), -2.5, 2.5)

def particles(model):
    return [t for t in model.turtles if isinstance(t, Particle)]


def mean_distance(model):
    sun = next(t for t in model.turtles if isinstance(t, Sun))
    ps = particles(model)
    return sum(p.distance(sun) for p in ps) / len(ps)


def mean_speed(model):
    ps = particles(model)
    return sum(math.hypot(p.vx, p.vy) for p in ps) / len(ps)


if __name__ == "__main__":
    run(
        Model(
            breeds={Sun: 1, Particle: 150},
            patch_class=Space,
            max_x=40,
            max_y=40,
            patch_size=8,
            metrics={"mean distance from sun": mean_distance, "mean speed": mean_speed},
        )
    )
