"""A pygame window that displays and drives a Model.

Layout is done in logical points and scaled by the display's pixel ratio when
drawing, so everything stays sharp on high-DPI (Retina) screens.
"""

import math
import time

import pygame
import pygame.gfxdraw

from .model import Model, Turtle

# --- Theme ----------------------------------------------------------------

BG = (13, 14, 18)
SURFACE = (22, 24, 30)
BORDER = (40, 43, 53)
BUTTON = (34, 37, 46)
BUTTON_HOVER = (45, 49, 60)
BUTTON_PRESSED = (28, 30, 38)
TEXT = (232, 234, 240)
TEXT_DIM = (130, 136, 152)
ACCENT = (99, 102, 241)
ACCENT_HOVER = (124, 128, 255)
ACCENT_PRESSED = (79, 82, 210)
RUNNING = (52, 211, 153)
STOPPED = (251, 191, 36)
TOOLTIP = (50, 54, 66)

UI_FONTS = "helveticaneue,avenirnext,segoeui,ubuntu,dejavusans,arial"
MONO_FONTS = "menlo,sfmono,consolas,dejavusansmono,couriernew"

# --- Layout (logical points) ----------------------------------------------

HEADER_HEIGHT = 60
FOOTER_HEIGHT = 34
MARGIN = 16
GAP = 8
BUTTON_HEIGHT = 34
BUTTON_WIDTHS = {"setup": 94, "go": 94, "step": 84}
SLIDER_WIDTH = 130
SLIDER_VALUE_WIDTH = 56
CORNER = 8
TOOLTIP_DELAY = 0.5
FPS = 60

# Turtle outline in turtle-local coordinates for a size-1 turtle: x is to the
# turtle's right, y is straight ahead.
TURTLE_SHAPE = [(0.0, 0.5), (0.4, -0.45), (0.0, -0.2), (-0.4, -0.45)]
TURTLE_RADIUS = 0.5


class Button:
    def __init__(self, name: str, rect: pygame.Rect, tooltip: str, primary=False):
        self.name = name
        self.rect = rect
        self.tooltip = tooltip
        self.primary = primary


class App:
    def __init__(self, model: Model, title: str):
        self.model = model
        self.title = title
        pygame.init()

        # Fonts must be measured before layout, but sized for the pixel ratio,
        # which isn't known until the window exists. Measure at 1x first.
        title_w = pygame.font.SysFont(UI_FONTS, 17, bold=True).size(title)[0]
        controls_w = (
            sum(BUTTON_WIDTHS.values()) + 2 * GAP + 24 + SLIDER_WIDTH + SLIDER_VALUE_WIDTH
        )

        ps = model.patch_size
        self.view_w = model.width * ps
        self.view_h = model.height * ps
        win_w = max(self.view_w + 2 * MARGIN, MARGIN + title_w + 32 + controls_w + MARGIN)
        win_h = HEADER_HEIGHT + MARGIN + self.view_h + MARGIN + FOOTER_HEIGHT
        self.win_w, self.win_h = win_w, win_h

        self.window = pygame.Window(title, (win_w, win_h), allow_high_dpi=True)
        self.screen = self.window.get_surface()
        self.dpr = self.screen.get_width() / win_w

        self.font = pygame.font.SysFont(UI_FONTS, self.px(13))
        self.font_bold = pygame.font.SysFont(UI_FONTS, self.px(13), bold=True)
        self.font_title = pygame.font.SysFont(UI_FONTS, self.px(17), bold=True)
        self.font_mono = pygame.font.SysFont(MONO_FONTS, self.px(12))
        self.clock = pygame.time.Clock()

        # World view, drawn at full pixel resolution.
        self.view_rect = pygame.Rect(
            (win_w - self.view_w) // 2, HEADER_HEIGHT + MARGIN, self.view_w, self.view_h
        )
        view_px = self.px_rect(self.view_rect).size
        self.view = pygame.Surface(view_px)
        # One pixel per patch, scaled up to the view when drawn.
        self.patch_pixels = pygame.Surface((model.width, model.height))
        # Background-colored overlay that rounds off the view's corners.
        self.corners = pygame.Surface(view_px, pygame.SRCALPHA)
        self.corners.fill(BG)
        pygame.draw.rect(
            self.corners, (0, 0, 0, 0), self.corners.get_rect(), border_radius=self.px(CORNER)
        )

        # Header controls, right-aligned.
        y = (HEADER_HEIGHT - BUTTON_HEIGHT) // 2
        x = win_w - MARGIN - SLIDER_VALUE_WIDTH - SLIDER_WIDTH
        self.slider_rect = pygame.Rect(x, y, SLIDER_WIDTH, BUTTON_HEIGHT)
        x -= 24
        self.buttons: list[Button] = []
        for name, tip, primary in reversed(
            [("setup", "Setup  (S)", False), ("go", "Run / pause  (Space)", True), ("step", "Step one tick  (T)", False)]
        ):
            w = BUTTON_WIDTHS[name]
            x -= w
            self.buttons.insert(0, Button(name, pygame.Rect(x, y, w, BUTTON_HEIGHT), tip, primary))
            x -= GAP

        self.speed = 0.5  # 0..1, see steps_per_second
        self.dragging_slider = False
        self.mouse = (-1, -1)
        self.pressed: Button | None = None
        self.hovered: Button | None = None
        self.hover_since = 0.0
        self.hand_cursor = False

        self.running = False
        self.stopped_by_model = False
        self.pending_steps = 0.0
        self.rate_time = time.perf_counter()
        self.rate_ticks = 0
        self.tick_rate = 0.0

    # --- Scaling ----------------------------------------------------------

    def px(self, v: float) -> int:
        return round(v * self.dpr)

    def px_rect(self, r: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(self.px(r.x), self.px(r.y), self.px(r.w), self.px(r.h))

    # --- Running ----------------------------------------------------------

    def steps_per_second(self) -> float:
        # Logarithmic: 1 tick/sec at the left, ~300 at the right.
        return 10 ** (self.speed * 2.5)

    def run(self) -> None:
        self.model.do_setup()
        while True:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.WINDOWCLOSE):
                    self.window.destroy()
                    pygame.quit()
                    return
                self.handle(event)
            self.advance(dt)
            self.draw()
            self.window.flip()

    def advance(self, dt: float) -> None:
        if self.running:
            self.pending_steps += dt * self.steps_per_second()
            # Cap work per frame so the UI stays responsive.
            self.pending_steps = min(self.pending_steps, 50)
            while self.running and self.pending_steps >= 1:
                self.pending_steps -= 1
                if not self.model.step():
                    self.running = False
                    self.stopped_by_model = True

        now = time.perf_counter()
        if now - self.rate_time >= 0.5:
            ticks = self.model.ticks - self.rate_ticks
            self.tick_rate = max(0, ticks) / (now - self.rate_time) if self.running else 0.0
            self.rate_time, self.rate_ticks = now, self.model.ticks

    def press(self, name: str) -> None:
        self.stopped_by_model = False
        if name == "setup":
            self.running = False
            self.model.do_setup()
            self.rate_ticks = 0
        elif name == "go":
            self.running = not self.running
            self.pending_steps = 0.0
        elif name == "step":
            self.running = False
            if not self.model.step():
                self.stopped_by_model = True

    # --- Input ------------------------------------------------------------

    def button_at(self, pos) -> Button | None:
        return next((b for b in self.buttons if b.rect.collidepoint(pos)), None)

    def set_speed_from(self, x: float) -> None:
        r = self.slider_rect
        self.speed = min(1.0, max(0.0, (x - r.left) / r.width))

    def handle(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self.mouse = event.pos
            if self.dragging_slider:
                self.set_speed_from(event.pos[0])
            hovered = self.button_at(event.pos)
            if hovered is not self.hovered:
                self.hovered = hovered
                self.hover_since = time.perf_counter()
            over_control = bool(hovered or self.slider_rect.collidepoint(event.pos))
            if over_control != self.hand_cursor:
                self.hand_cursor = over_control
                try:
                    pygame.mouse.set_cursor(
                        pygame.SYSTEM_CURSOR_HAND if over_control else pygame.SYSTEM_CURSOR_ARROW
                    )
                except pygame.error:  # e.g. headless video drivers
                    pass
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.pressed = self.button_at(event.pos)
            if self.slider_rect.collidepoint(event.pos):
                self.dragging_slider = True
                self.set_speed_from(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # Buttons fire on release, only if still over the pressed button.
            if self.pressed is not None and self.pressed is self.button_at(event.pos):
                self.press(self.pressed.name)
            self.pressed = None
            self.dragging_slider = False
        elif event.type == pygame.WINDOWLEAVE:
            self.mouse = (-1, -1)
            self.hovered = None
        elif event.type == pygame.KEYDOWN:
            keys = {pygame.K_s: "setup", pygame.K_g: "go", pygame.K_SPACE: "go", pygame.K_t: "step"}
            if event.key in keys:
                self.press(keys[event.key])

    # --- Drawing ----------------------------------------------------------

    def text(self, s: str, font: pygame.font.Font, color, **anchor) -> pygame.Rect:
        """Draw text positioned by a logical-point anchor, e.g. midleft=(x, y)."""
        surf = font.render(s, True, color)
        (name, (x, y)), = anchor.items()
        rect = surf.get_rect(**{name: (self.px(x), self.px(y))})
        self.screen.blit(surf, rect)
        return rect

    def draw(self) -> None:
        self.screen.fill(BG)
        self.draw_view()
        self.draw_header()
        self.draw_footer()
        self.draw_tooltip()

    def draw_view(self) -> None:
        m = self.model
        with pygame.PixelArray(self.patch_pixels) as pixels:
            for p in m.patches:
                pixels[p.x + m.max_x, m.max_y - p.y] = p.color
        pygame.transform.scale(self.patch_pixels, self.view.get_size(), self.view)
        for t in m.turtles:
            self.draw_turtle(t)
        dest = self.px_rect(self.view_rect)
        self.screen.blit(self.view, dest)
        self.screen.blit(self.corners, dest)
        pygame.draw.rect(
            self.screen, BORDER, dest.inflate(2, 2), width=max(1, self.px(1)),
            border_radius=self.px(CORNER) + 1,
        )

    def draw_turtle(self, t: Turtle) -> None:
        m = self.model
        scale = m.patch_size * self.dpr
        rad = math.radians(t.heading)
        sin, cos = math.sin(rad), math.cos(rad)
        # Rotate clockwise by heading: "ahead" maps to (sin, cos).
        local = [
            (lx * t.size * cos + ly * t.size * sin, -lx * t.size * sin + ly * t.size * cos)
            for lx, ly in TURTLE_SHAPE
        ]
        # A turtle overlapping an edge is also drawn on the opposite side.
        r = TURTLE_RADIUS * t.size
        x_offsets, y_offsets = [0], [0]
        if t.x + r > m.max_x + 0.5:
            x_offsets.append(-m.width)
        if t.x - r < -m.max_x - 0.5:
            x_offsets.append(m.width)
        if t.y + r > m.max_y + 0.5:
            y_offsets.append(-m.height)
        if t.y - r < -m.max_y - 0.5:
            y_offsets.append(m.height)
        for ox in x_offsets:
            for oy in y_offsets:
                cx = (t.x + ox + m.max_x + 0.5) * scale
                cy = (m.max_y + 0.5 - t.y - oy) * scale
                points = [(round(cx + dx * scale), round(cy - dy * scale)) for dx, dy in local]
                pygame.gfxdraw.filled_polygon(self.view, points, t.color)
                pygame.gfxdraw.aapolygon(self.view, points, t.color)

    def draw_header(self) -> None:
        bar = pygame.Rect(0, 0, self.win_w, HEADER_HEIGHT)
        pygame.draw.rect(self.screen, SURFACE, self.px_rect(bar))
        pygame.draw.line(
            self.screen, BORDER, (0, self.px(HEADER_HEIGHT) - 1),
            (self.px(self.win_w), self.px(HEADER_HEIGHT) - 1), max(1, self.px(1)),
        )
        self.text(self.title, self.font_title, TEXT, midleft=(MARGIN, HEADER_HEIGHT / 2))
        for b in self.buttons:
            self.draw_button(b)
        self.draw_slider()

    def draw_button(self, b: Button) -> None:
        hovered = b is self.hovered
        pressed = b is self.pressed and hovered
        if b.primary:
            fill = ACCENT_PRESSED if pressed else ACCENT_HOVER if hovered else ACCENT
        else:
            fill = BUTTON_PRESSED if pressed else BUTTON_HOVER if hovered else BUTTON
        rect = self.px_rect(b.rect)
        if pressed:
            rect = rect.move(0, self.px(1))
        pygame.draw.rect(self.screen, fill, rect, border_radius=self.px(8))
        if not b.primary:
            pygame.draw.rect(self.screen, BORDER, rect, width=max(1, self.px(1)), border_radius=self.px(8))

        label = {"setup": "Setup", "go": "Pause" if self.running else "Go", "step": "Step"}[b.name]
        label_surf = self.font_bold.render(label, True, TEXT)
        icon = self.px(12)
        gap = self.px(7)
        left = rect.centerx - (icon + gap + label_surf.get_width()) // 2
        self.draw_icon(b.name, pygame.Rect(left, rect.centery - icon // 2, icon, icon))
        self.screen.blit(label_surf, label_surf.get_rect(midleft=(left + icon + gap, rect.centery)))

    def draw_icon(self, name: str, r: pygame.Rect) -> None:
        if name == "go" and self.running:  # pause bars
            w = r.width // 3
            pygame.draw.rect(self.screen, TEXT, (r.left, r.top, w, r.height), border_radius=self.px(1))
            pygame.draw.rect(self.screen, TEXT, (r.right - w, r.top, w, r.height), border_radius=self.px(1))
        elif name == "go":  # play triangle
            self.aa_polygon([(r.left + self.px(1), r.top), (r.right, r.centery), (r.left + self.px(1), r.bottom)], TEXT)
        elif name == "step":  # triangle and bar
            bar = max(2, self.px(2))
            self.aa_polygon([(r.left, r.top), (r.right - bar - self.px(1), r.centery), (r.left, r.bottom)], TEXT)
            pygame.draw.rect(self.screen, TEXT, (r.right - bar, r.top, bar, r.height))
        elif name == "setup":  # circular arrow
            width = max(2, self.px(2))
            radius = r.width / 2 - width / 2
            arc = r.inflate(-width + 1, -width + 1)
            start = math.radians(10)
            pygame.draw.arc(self.screen, TEXT, arc, start, math.radians(280), width)
            # Arrowhead at the arc's start, pointing clockwise along the arc.
            ax = r.centerx + radius * math.cos(start)
            ay = r.centery - radius * math.sin(start)
            tx, ty = math.sin(start), math.cos(start)  # clockwise tangent
            nx, ny = math.cos(start), -math.sin(start)  # outward normal
            s = self.px(3.5)
            self.aa_polygon(
                [(ax + nx * s, ay + ny * s), (ax - nx * s, ay - ny * s), (ax + tx * s * 1.2, ay + ty * s * 1.2)],
                TEXT,
            )

    def aa_polygon(self, points, color) -> None:
        points = [(round(x), round(y)) for x, y in points]
        pygame.gfxdraw.filled_polygon(self.screen, points, color)
        pygame.gfxdraw.aapolygon(self.screen, points, color)

    def draw_slider(self) -> None:
        r = self.slider_rect
        cy = self.px(r.centery + 6)
        x0, x1 = self.px(r.left), self.px(r.right)
        knob_x = x0 + round(self.speed * (x1 - x0))
        track = max(2, self.px(4))
        pygame.draw.line(self.screen, BORDER, (x0, cy), (x1, cy), track)
        pygame.draw.line(self.screen, ACCENT, (x0, cy), (knob_x, cy), track)
        active = self.dragging_slider or r.collidepoint(self.mouse)
        radius = self.px(8 if active else 7)
        pygame.gfxdraw.aacircle(self.screen, knob_x, cy, radius, TEXT)
        pygame.gfxdraw.filled_circle(self.screen, knob_x, cy, radius, TEXT)
        self.text("SPEED", self.font_mono, TEXT_DIM, bottomleft=(r.left, r.centery - 2))
        sps = self.steps_per_second()
        value = f"{sps:.0f}/s" if sps >= 10 else f"{sps:.1f}/s"
        self.text(value, self.font_mono, TEXT, midleft=(r.right + 14, r.centery + 6))

    def draw_footer(self) -> None:
        top = self.win_h - FOOTER_HEIGHT
        cy = top + FOOTER_HEIGHT / 2
        pygame.draw.rect(self.screen, SURFACE, self.px_rect(pygame.Rect(0, top, self.win_w, FOOTER_HEIGHT)))
        pygame.draw.line(
            self.screen, BORDER, (0, self.px(top)), (self.px(self.win_w), self.px(top)), max(1, self.px(1))
        )

        if self.running:
            status, color = "running", RUNNING
        elif self.stopped_by_model:
            status, color = "stopped", STOPPED
        else:
            status, color = "paused", TEXT_DIM
        dot = self.px(4)
        pygame.gfxdraw.aacircle(self.screen, self.px(MARGIN + 4), self.px(cy), dot, color)
        pygame.gfxdraw.filled_circle(self.screen, self.px(MARGIN + 4), self.px(cy), dot, color)
        x = MARGIN + 14
        x = self.text(status, self.font_mono, color, midleft=(x, cy)).right / self.dpr + 20

        m = self.model
        for label, value in (("tick", m.ticks), ("turtles", len(m.turtles)), ("patches", len(m.patches))):
            x = self.text(label, self.font_mono, TEXT_DIM, midleft=(x, cy)).right / self.dpr + 6
            x = self.text(f"{value:,}", self.font_mono, TEXT, midleft=(x, cy)).right / self.dpr + 18

        rate = f"{self.tick_rate:.0f} ticks/s · {self.clock.get_fps():.0f} fps"
        self.text(rate, self.font_mono, TEXT_DIM, midright=(self.win_w - MARGIN, cy))

    def draw_tooltip(self) -> None:
        b = self.hovered
        if b is None or self.pressed or time.perf_counter() - self.hover_since < TOOLTIP_DELAY:
            return
        surf = self.font.render(b.tooltip, True, TEXT)
        pad_x, pad_y = self.px(8), self.px(5)
        box = surf.get_rect().inflate(2 * pad_x, 2 * pad_y)
        box.midtop = (self.px(b.rect.centerx), self.px(b.rect.bottom + 8))
        box.right = min(box.right, self.px(self.win_w - 4))
        pygame.draw.rect(self.screen, TOOLTIP, box, border_radius=self.px(6))
        pygame.draw.rect(self.screen, BORDER, box, width=max(1, self.px(1)), border_radius=self.px(6))
        self.screen.blit(surf, surf.get_rect(center=box.center))


def run(model: Model, title: str | None = None) -> None:
    """Open a window for `model` and run it until the window is closed."""
    if title is None:
        if type(model) is Model and model.breeds:
            title = ", ".join(cls.__name__ for cls in model.breeds)
        else:
            title = type(model).__name__
    App(model, title).run()
