# emerge

A NetLogo-like agent-based modeling library in plain Python. Users write models by
subclassing `Turtle` / `Patch` (and optionally `Model`), and `run(model)` opens a pygame GUI.

## Commands

- `uv run pytest`: run the tests (headless; `tests/conftest.py` sets `SDL_VIDEODRIVER=dummy`)
- `uv run examples/<name>.py`: run an example in a window
- `uv run examples/<name>.py --headless --ticks 500`: run without a window (see `--help`)

To look at the GUI without a display, construct `emerge.gui.App`, call `app.draw()`, and
save `app.screen` with `pygame.image.save`. Under the dummy driver the pixel ratio is 1x;
real Retina windows render at 2x.

## Design rules

- Follow NetLogo semantics and names (snake_cased): `face`, `towards`, `scale_color`, etc.
  The origin is at the center, y points up, heading 0 is north and increases clockwise, and
  the world wraps; anything measuring between points takes the short way around
  (`Model.offset`).
- Users never write `__init__`. Behavior goes in `setup()` / `step()` hooks; the model
  constructs agents and calls `setup()` itself.
- Keep per-patch work cheap: worlds can have tens of thousands of patches. That's why
  `Model.go` skips patch stepping when `step` isn't overridden, and the GUI draws patches as
  one pixel each, then scales.
- Each new feature gets tests, a README mention, and usually an example in `examples/`.
- The GUI uses pygame-ce, not tkinter: Homebrew's Python ships without Tk.
