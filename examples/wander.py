"""Turtles wander randomly, turning red in the east half and blue in the west."""

import random

from emerge import Model, Turtle, run


class Wanderer(Turtle):
    def step(self):
        self.right(random.uniform(-30, 30))
        self.forward(0.5)
        self.color = "red" if self.x > 0 else "blue"


if __name__ == "__main__":
    run(Model(breeds={Wanderer: 100}))
