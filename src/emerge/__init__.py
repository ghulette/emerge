"""emerge: a small NetLogo-like agent-based modeling library, in plain Python."""

from . import colors
from .colors import scale_color
from .gui import run
from .model import Model, Patch, Turtle

__all__ = ["Model", "Patch", "Turtle", "colors", "run", "scale_color"]
