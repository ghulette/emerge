"""emerge: a small NetLogo-like agent-based modeling library, in plain Python."""

from . import colors
from .gui import run
from .model import Model, Turtle

__all__ = ["Model", "Turtle", "colors", "run"]
