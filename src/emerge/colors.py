"""Named colors, modeled on NetLogo's base colors.

Anywhere a color is accepted you can pass one of these names (e.g. "red"),
or an (r, g, b) tuple with components in 0-255.
"""

import random as _random

Color = tuple[int, int, int]

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


def to_rgb(color: str | Color) -> Color:
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
