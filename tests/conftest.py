import importlib.util
import os
from pathlib import Path

import pytest

# Run pygame headlessly and quietly. Must happen before emerge imports pygame.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from emerge import Model  # noqa: E402

EXAMPLES = Path(__file__).parent.parent / "examples"


def load_example(name: str):
    """Import examples/<name>.py as a module (examples aren't a package)."""
    spec = importlib.util.spec_from_file_location(f"examples.{name}", EXAMPLES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def model():
    """A small, set-up world: patches -3..3 by -2..2, no turtles."""
    m = Model(max_x=3, max_y=2)
    m.do_setup()
    return m
