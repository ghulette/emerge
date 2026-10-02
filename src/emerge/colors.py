"""Named colors, modeled on NetLogo's base colors.

Anywhere a color is accepted you can pass one of these names (e.g. "red"),
or an (r, g, b) tuple with components in 0-255.
"""

import random as _random

Color = tuple[int, int, int]
# Anything accepted as a color: a name, or an (r, g, b) tuple.
ColorLike = str | tuple[float, float, float]

BASE_COLORS: dict[str, Color] = {
    "gray": (141, 141, 141),
    "red": (215, 50, 41),
    "orange": (241, 106, 21),
    "brown": (157, 110, 72),
    "yellow": (237, 237, 49),
    "green": (89, 176, 60),
    "lime": (44, 209, 59),
    "turquoise": (29, 159, 120),
    "cyan": (84, 196, 196),
    "sky": (45, 141, 190),
    "blue": (52, 93, 169),
    "violet": (124, 80, 164),
    "magenta": (167, 27, 106),
    "pink": (224, 127, 150),
}

NAMED_COLORS: dict[str, Color] = {
    **BASE_COLORS,
    "grey": BASE_COLORS["gray"],
    "black": (0, 0, 0),
    "white": (255, 255, 255),
}


def to_rgb(color: ColorLike) -> Color:
    """Normalize a color name or RGB tuple to an RGB tuple."""
    if isinstance(color, str):
        try:
            return NAMED_COLORS[color.lower()]
        except KeyError:
            raise ValueError(f"unknown color name: {color!r}") from None
    r, g, b = color
    return (int(r), int(g), int(b))


def random() -> Color:
    """A random base color."""
    return _random.choice(list(BASE_COLORS.values()))


def scale_color(color: ColorLike, value: float, low: float, high: float) -> Color:
    """A shade of `color` for where `value` falls between `low` and `high`.

    Like NetLogo's scale-color: `low` maps to black, the midpoint to `color`
    itself, and `high` to white. Values outside the range are clamped. If
    `low` is greater than `high`, the scale runs the other way.
    """
    base = to_rgb(color)
    if low == high:
        t = 0.5
    else:
        t = min(1.0, max(0.0, (value - low) / (high - low)))
    if t < 0.5:
        a, b, f = (0, 0, 0), base, t * 2
    else:
        a, b, f = base, (255, 255, 255), t * 2 - 1
    return (
        round(a[0] + (b[0] - a[0]) * f),
        round(a[1] + (b[1] - a[1]) * f),
        round(a[2] + (b[2] - a[2]) * f),
    )
