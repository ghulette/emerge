"""Turtles start on a ring, each tracing its own circle, cycling through colors."""

from emerge import Model, Turtle, colors, run

PALETTE = list(colors.BASE_COLORS)


class Circler(Turtle):
    def setup(self):
        self.forward(10)
        self.right(90)

    def step(self):
        self.fd(0.3)
        self.lt(2)
        ticks = self.model.ticks
        if ticks % 20 == 0:
            self.color = PALETTE[(ticks // 20) % len(PALETTE)]
        if ticks >= 2000:
            self.model.stop()


if __name__ == "__main__":
    run(Model(breeds={Circler: 36}, max_x=25, max_y=25, patch_size=10))
