"""Conway's Game of Life, using only patches.

Every cell must update at once, based on its neighbors' states from the
previous tick, so the model does it in two passes: first every cell counts its
live neighbors, then every cell updates. The run stops when the board stops
changing.
"""

import random

from emerge import Model, Patch, run

INITIAL_DENSITY = 0.3


class Cell(Patch):
    def setup(self):
        self.set_alive(random.random() < INITIAL_DENSITY)

    def set_alive(self, alive):
        self.alive = alive
        self.color = "lime" if alive else "black"

    def count_neighbors(self):
        self.live_neighbors = sum(n.alive for n in self.neighbors)

    def update(self):
        """Apply the rules. Returns True if the cell changed."""
        alive = self.live_neighbors == 3 or (self.alive and self.live_neighbors == 2)
        if alive == self.alive:
            return False
        self.set_alive(alive)
        return True


class Life(Model[Cell]):
    patch_class = Cell
    max_x = 50
    max_y = 40
    patch_size = 7

    def go(self):
        for cell in self.patches:
            cell.count_neighbors()
        changed = [cell.update() for cell in self.patches]
        if not any(changed):
            self.stop()


if __name__ == "__main__":
    run(Life())
