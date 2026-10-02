"""Wolf-sheep predation, after NetLogo's classic model (with grass).

Sheep wander and eat grass; wolves wander and eat sheep. Moving costs energy,
eating restores it, animals with energy below zero die, and each tick an
animal may reproduce, splitting its energy with its offspring. Eaten grass
regrows after a fixed time. The populations rise and fall in cycles, which
the population chart shows.
"""

import random

from emerge import Model, Patch, Turtle, run

INITIAL_SHEEP = 100
INITIAL_WOLVES = 50
SHEEP_GAIN_FROM_FOOD = 4
WOLF_GAIN_FROM_FOOD = 20
SHEEP_REPRODUCE = 0.04  # chance per tick
WOLF_REPRODUCE = 0.05
GRASS_REGROWTH_TIME = 30


class Grass(Patch):
    def setup(self):
        self.grown = random.random() < 0.5
        self.countdown = GRASS_REGROWTH_TIME if self.grown else random.randrange(GRASS_REGROWTH_TIME)
        self.color = "green" if self.grown else "brown"

    def step(self):
        if not self.grown:
            self.countdown -= 1
            if self.countdown <= 0:
                self.grown = True
                self.countdown = GRASS_REGROWTH_TIME
                self.color = "green"

    def eat(self):
        self.grown = False
        self.color = "brown"


class Animal(Turtle):
    gain_from_food = 0
    reproduce_chance = 0.0

    def setup(self):
        self.size = 1.8
        self.energy = random.randrange(2 * self.gain_from_food)
        self.move_to(random.choice(self.model.patches))

    def step(self):
        self.right(random.uniform(0, 50))
        self.left(random.uniform(0, 50))
        self.forward(1)
        self.energy -= 1
        self.eat()
        if self.energy < 0:
            self.die()
        elif random.random() < self.reproduce_chance:
            self.energy /= 2
            for child in self.hatch():
                child.right(random.uniform(0, 360))
                child.forward(1)

    def eat(self):
        pass


class Sheep(Animal):
    shape = "🐑"
    gain_from_food = SHEEP_GAIN_FROM_FOOD
    reproduce_chance = SHEEP_REPRODUCE

    def eat(self):
        grass = self.patch
        if grass.grown:
            grass.eat()
            self.energy += self.gain_from_food


class Wolf(Animal):
    shape = "🐺"
    gain_from_food = WOLF_GAIN_FROM_FOOD
    reproduce_chance = WOLF_REPRODUCE

    def eat(self):
        prey = [t for t in self.patch.turtles if isinstance(t, Sheep)]
        if prey:
            random.choice(prey).die()
            self.energy += self.gain_from_food


def population(model):
    sheep = sum(isinstance(t, Sheep) for t in model.turtles)
    return {"sheep": sheep, "wolves": len(model.turtles) - sheep}


def grass_percent(model):
    return 100 * sum(p.grown for p in model.patches) / len(model.patches)


def model():
    return Model(
        breeds={Sheep: INITIAL_SHEEP, Wolf: INITIAL_WOLVES},
        patch_class=Grass,
        max_x=25,
        max_y=25,
        patch_size=13,
        metrics={"population": population, "grass %": grass_percent},
    )


if __name__ == "__main__":
    run(model())
