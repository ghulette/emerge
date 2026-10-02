"""A pygame window that displays and drives a Model."""

import math

import pygame

from .model import Model, Turtle

TOOLBAR_HEIGHT = 44
PADDING = 8
BUTTON_WIDTH = 64
SLIDER_WIDTH = 120
MIN_WINDOW_WIDTH = 3 * (BUTTON_WIDTH + PADDING) + SLIDER_WIDTH + 140
FPS = 60

TOOLBAR_BG = (232, 232, 232)
BUTTON_BG = (250, 250, 250)
BUTTON_ACTIVE_BG = (40, 40, 40)
TEXT = (30, 30, 30)
TEXT_ACTIVE = (250, 250, 250)
BORDER = (160, 160, 160)

# Turtle outline in turtle-local coordinates for a size-1 turtle: x is to the
# turtle's right, y is straight ahead.
TURTLE_SHAPE = [(0.0, 0.5), (0.4, -0.45), (0.0, -0.2), (-0.4, -0.45)]


class Button:
    def __init__(self, label: str, rect: pygame.Rect):
        self.label = label
        self.rect = rect

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, active=False):
        bg, fg = (BUTTON_ACTIVE_BG, TEXT_ACTIVE) if active else (BUTTON_BG, TEXT)
        pygame.draw.rect(surface, bg, self.rect, border_radius=4)
        pygame.draw.rect(surface, BORDER, self.rect, width=1, border_radius=4)
        text = font.render(self.label, True, fg)
        surface.blit(text, text.get_rect(center=self.rect.center))


class Slider:
    def __init__(self, label: str, rect: pygame.Rect, value: float):
        self.label = label
        self.rect = rect
        self.value = value  # 0..1
        self.dragging = False

    def handle(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.dragging = True
            self._set_from(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from(event.pos[0])

    def _set_from(self, px: int) -> None:
        self.value = min(1.0, max(0.0, (px - self.rect.left) / self.rect.width))

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        label = font.render(self.label, True, TEXT)
        surface.blit(label, (self.rect.left, self.rect.top - 2))
        track_y = self.rect.bottom - 6
        pygame.draw.line(
            surface, BORDER, (self.rect.left, track_y), (self.rect.right, track_y), 2
        )
        knob_x = self.rect.left + self.value * self.rect.width
        pygame.draw.circle(surface, BUTTON_ACTIVE_BG, (knob_x, track_y), 6)


class App:
    def __init__(self, model: Model, title: str):
        self.model = model
        pygame.init()
        pygame.display.set_caption(title)

        ps = model.patch_size
        self.view_w = model.width * ps
        self.view_h = model.height * ps
        win_w = max(self.view_w, MIN_WINDOW_WIDTH)
        self.screen = pygame.display.set_mode((win_w, TOOLBAR_HEIGHT + self.view_h))
        self.view = pygame.Surface((self.view_w, self.view_h))
        # One pixel per patch, scaled up to the view when drawn.
        self.patch_pixels = pygame.Surface((model.width, model.height))
        self.view_pos = ((win_w - self.view_w) // 2, TOOLBAR_HEIGHT)
        self.font = pygame.font.SysFont(None, 20)
        self.clock = pygame.time.Clock()

        bh = TOOLBAR_HEIGHT - 2 * PADDING
        x = PADDING
        self.buttons: dict[str, Button] = {}
        for label in ("Setup", "Go", "Step"):
            self.buttons[label] = Button(label, pygame.Rect(x, PADDING, BUTTON_WIDTH, bh))
            x += BUTTON_WIDTH + PADDING
        self.speed = Slider("speed", pygame.Rect(x + PADDING, PADDING - 2, SLIDER_WIDTH, bh + 4), 0.5)
        self.ticks_x = x + SLIDER_WIDTH + 3 * PADDING

        self.running = False
        self.pending_steps = 0.0

    def steps_per_second(self) -> float:
        # Logarithmic: 1 tick/sec at the left, ~300 at the right.
        return 10 ** (self.speed.value * 2.5)

    def run(self) -> None:
        self.model.do_setup()
        while True:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                self.handle(event)

            if self.running:
                self.pending_steps += dt * self.steps_per_second()
                # Cap work per frame so the UI stays responsive.
                self.pending_steps = min(self.pending_steps, 50)
                while self.running and self.pending_steps >= 1:
                    self.pending_steps -= 1
                    if not self.model.step():
                        self.running = False

            self.draw()

    def handle(self, event: pygame.event.Event) -> None:
        self.speed.handle(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for label, button in self.buttons.items():
                if button.rect.collidepoint(event.pos):
                    self.press(label)
        elif event.type == pygame.KEYDOWN:
            key = {pygame.K_s: "Setup", pygame.K_g: "Go", pygame.K_SPACE: "Go", pygame.K_t: "Step"}
            if event.key in key:
                self.press(key[event.key])

    def press(self, label: str) -> None:
        if label == "Setup":
            self.running = False
            self.model.do_setup()
        elif label == "Go":
            self.running = not self.running
            self.pending_steps = 0.0
        elif label == "Step":
            self.running = False
            self.model.step()

    # --- Drawing --------------------------------------------------------

    def to_screen(self, x: float, y: float) -> tuple[float, float]:
        ps = self.model.patch_size
        return (
            (x + self.model.max_x + 0.5) * ps,
            (self.model.max_y + 0.5 - y) * ps,
        )

    def draw_turtle(self, t: Turtle) -> None:
        rad = math.radians(t.heading)
        sin, cos = math.sin(rad), math.cos(rad)
        points = []
        for lx, ly in TURTLE_SHAPE:
            lx, ly = lx * t.size, ly * t.size
            # Rotate clockwise by heading: "ahead" maps to (sin, cos).
            points.append(self.to_screen(t.x + lx * cos + ly * sin, t.y - lx * sin + ly * cos))
        pygame.draw.polygon(self.view, t.color, points)

    def draw_patches(self) -> None:
        m = self.model
        with pygame.PixelArray(self.patch_pixels) as pixels:
            for p in m.patches:
                pixels[p.x + m.max_x, m.max_y - p.y] = p.color
        pygame.transform.scale(self.patch_pixels, (self.view_w, self.view_h), self.view)

    def draw(self) -> None:
        self.screen.fill(TOOLBAR_BG)
        self.draw_patches()
        for t in self.model.turtles:
            self.draw_turtle(t)
        self.screen.blit(self.view, self.view_pos)

        for label, button in self.buttons.items():
            button.draw(self.screen, self.font, active=(label == "Go" and self.running))
        self.speed.draw(self.screen, self.font)
        ticks = self.font.render(f"ticks: {self.model.ticks}", True, TEXT)
        self.screen.blit(ticks, ticks.get_rect(midleft=(self.ticks_x, TOOLBAR_HEIGHT // 2)))
        pygame.display.flip()


def run(model: Model, title: str | None = None) -> None:
    """Open a window for `model` and run it until the window is closed."""
    if title is None:
        if type(model) is Model and model.breeds:
            title = ", ".join(cls.__name__ for cls in model.breeds)
        else:
            title = type(model).__name__
    App(model, title).run()
