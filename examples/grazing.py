"""Cows wander a field, eating grass as they go. Eaten grass slowly regrows."""

import random

from emerge import Model, Patch, Turtle, run

REGROW_CHANCE = 0.005


class Grass(Patch):
    def setup(self):
        self.grown = True
        self.color = "green"

    def step(self):
        if not self.grown and random.random() < REGROW_CHANCE:
            self.grown = True
            self.color = "green"


class Cow(Turtle):
    shape = "🐄"

    def setup(self):
        self.size = 1.6
        self.move_to(random.choice(self.model.patches))

    def step(self):
        self.right(random.uniform(-40, 40))
        self.forward(0.5)
        grass = self.patch
        if grass.grown:
            grass.grown = False
            grass.color = "brown"


if __name__ == "__main__":
    run(Model(breeds={Cow: 30}, patch_class=Grass, max_x=30, max_y=20, patch_size=10))
