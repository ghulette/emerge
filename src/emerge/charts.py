"""Live line charts of a model's metrics, drawn beside the world view."""

import time

import pygame

from .theme import BG, BORDER, SERIES, SURFACE, TEXT, TEXT_DIM

PANEL_WIDTH = 300
CHART_MAX_HEIGHT = 170
CHART_GAP = 10
# Redraw at most this often while running; drawing long histories isn't free.
REDRAW_INTERVAL = 0.1


def format_value(v: float | None) -> str:
    if v is None:
        return "–"
    if isinstance(v, int) or float(v).is_integer():
        return f"{int(v):,}"
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    if abs(v) >= 1:
        return f"{v:,.2f}"
    return f"{v:.3g}"


def columns(ticks: list[int], values: list[float | None], width: int):
    """Reduce a series to at most `width` columns of (tick, mean, low, high),
    skipping missing values. Short series keep one column per point.
    """
    points = [(t, v) for t, v in zip(ticks, values) if v is not None]
    if len(points) <= width:
        return [(t, v, v, v) for t, v in points]
    out = []
    per = len(points) / width
    for i in range(width):
        bucket = points[int(i * per) : int((i + 1) * per)]
        if bucket:
            vs = [v for _, v in bucket]
            out.append((bucket[-1][0], sum(vs) / len(vs), min(vs), max(vs)))
    return out


class ChartPanel:
    def __init__(self, app, rect: pygame.Rect):
        self.app = app
        self.rect = rect  # logical points
        self.surface = pygame.Surface(app.px_rect(rect).size)
        self.drawn_len = -1
        self.drawn_at = 0.0

    def draw(self, screen: pygame.Surface) -> None:
        history = self.app.model.history
        n = len(history["tick"])
        now = time.perf_counter()
        stale = n != self.drawn_len
        throttled = self.app.running and now - self.drawn_at < REDRAW_INTERVAL
        if stale and not throttled:
            self.render(history)
            self.drawn_len, self.drawn_at = n, now
        screen.blit(self.surface, self.app.px_rect(self.rect))

    def render(self, history: dict[str, list]) -> None:
        app = self.app
        self.surface.fill(BG)
        names = [name for name in history if name != "tick"]
        if not names:
            return
        h = min(CHART_MAX_HEIGHT, (self.rect.height - CHART_GAP * (len(names) - 1)) / len(names))
        for i, name in enumerate(names):
            card = pygame.Rect(0, round(i * (h + CHART_GAP)), self.rect.width, round(h))
            self.render_chart(card, name, history["tick"], history[name], SERIES[i % len(SERIES)])

    def render_chart(self, card: pygame.Rect, name: str, ticks: list, values: list, color) -> None:
        app, px, surf = self.app, self.app.px, self.surface
        box = pygame.Rect(px(card.x), px(card.y), px(card.width), px(card.height))
        pygame.draw.rect(surf, SURFACE, box, border_radius=px(8))
        pygame.draw.rect(surf, BORDER, box, width=max(1, px(1)), border_radius=px(8))

        # Header: name and current value.
        pad = 12
        label = app.font_mono.render(name, True, TEXT_DIM)
        surf.blit(label, label.get_rect(topleft=(px(card.x + pad), px(card.y + pad))))
        latest = next((v for v in reversed(values) if v is not None), None)
        value = app.font_bold.render(format_value(latest), True, TEXT)
        surf.blit(value, value.get_rect(topright=(px(card.right - pad), px(card.y + pad - 1))))

        present = [t for t, v in zip(ticks, values) if v is not None]
        if not present:
            return
        present_values = [v for v in values if v is not None]
        lo, hi = min(present_values), max(present_values)
        if lo == hi:
            lo, hi = lo - 1, hi + 1
        # Leave a gutter on the left for the min/max labels.
        gutter = max(app.font_small.size(format_value(v))[0] for v in (lo, hi)) / app.dpr + 8
        plot = pygame.Rect(
            px(card.x + pad + gutter),
            px(card.y + pad + 24),
            px(card.width - 2 * pad - gutter),
            px(card.height - 2 * pad - 24 - 16),
        )
        if plot.height < px(10):
            return
        cols = columns(ticks, values, plot.width // max(1, px(1)))
        t0, t1 = present[0], present[-1]
        span = max(1, t1 - t0)

        def x(t):
            return plot.left + (t - t0) / span * plot.width

        def y(v):
            return plot.bottom - (v - lo) / (hi - lo) * plot.height

        # Faint grid line at the middle, then min/max labels.
        mid = plot.centery
        pygame.draw.line(surf, BORDER, (plot.left, mid), (plot.right, mid), max(1, px(1)))
        for v, anchor in ((hi, "topright"), (lo, "bottomright")):
            text = app.font_small.render(format_value(v), True, TEXT_DIM)
            surf.blit(text, text.get_rect(**{anchor: (plot.left - px(6), y(v))}))
        for t, anchor in ((t0, "topleft"), (t1, "topright")):
            text = app.font_small.render(f"{t:,}", True, TEXT_DIM)
            surf.blit(text, text.get_rect(**{anchor: (plot.left if anchor == "topleft" else plot.right, plot.bottom + px(4))}))

        line = [(x(t), y(mean)) for t, mean, _, _ in cols]
        if len(line) == 1:
            pygame.draw.circle(surf, color, line[0], px(2.5))
            return

        # Translucent fill under the line, plus the min/max envelope when
        # several ticks share a column.
        overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        area = [(line[0][0], plot.bottom), *line, (line[-1][0], plot.bottom)]
        pygame.draw.polygon(overlay, (*color, 38), area)
        if any(low != high for _, _, low, high in cols):
            band = [(x(t), y(high)) for t, _, _, high in cols] + [(x(t), y(low)) for t, _, low, _ in reversed(cols)]
            pygame.draw.polygon(overlay, (*color, 70), band)
        surf.blit(overlay, (0, 0))
        pygame.draw.lines(surf, color, False, line, max(2, px(1.5)))
        end = line[-1]
        pygame.draw.circle(surf, color, end, px(3))
