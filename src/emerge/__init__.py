"""emerge: a small NetLogo-like agent-based modeling library, in plain Python."""

import os

# pygame prints a banner on import; keep model output clean.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from . import colors  # noqa: E402
from .colors import scale_color  # noqa: E402
from .model import Model, Patch, Turtle  # noqa: E402
from .runner import run  # noqa: E402

__all__ = ["Model", "Patch", "Turtle", "colors", "run", "scale_color"]
