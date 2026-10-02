"""`run`: the entry point for model scripts, with command-line options."""

import argparse
import csv
import random
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .charts import format_value
from .model import Model


def parser(description: str | None = None) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--go", action="store_true", help="start running right away")
    p.add_argument(
        "--speed", type=float, metavar="N", help="ticks per second (1 to ~300; default ~18)"
    )
    p.add_argument("--ticks", type=int, metavar="N", help="stop after N ticks")
    p.add_argument("--seed", type=int, metavar="N", help="random seed, for reproducible runs")
    p.add_argument(
        "--headless",
        action="store_true",
        help="run without a window (requires --ticks) and print the final metrics",
    )
    p.add_argument(
        "--csv",
        type=Path,
        metavar="PATH",
        help="write the metrics history to a CSV file when the run ends",
    )
    return p


def write_csv(history: dict[str, list], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(history)
        writer.writerows(zip(*history.values()))


def run(model: Model[Any], title: str | None = None, args: Sequence[str] | None = None) -> None:
    """Run `model`, by default in a window, configured by command-line
    options (see `--help`). `args` defaults to `sys.argv[1:]`; pass `[]` to
    ignore the command line.
    """
    # Show the model script's docstring in --help.
    description = getattr(sys.modules.get("__main__"), "__doc__", None)
    options = parser(description).parse_args(sys.argv[1:] if args is None else args)
    if options.headless and options.ticks is None:
        parser().error("--headless requires --ticks")
    if options.ticks is not None and options.ticks < 0:
        parser().error("--ticks must be at least 0")
    if options.seed is not None:
        random.seed(options.seed)

    if options.headless:
        assert options.ticks is not None
        history = model.simulate(options.ticks)
        print(f"ran {model.ticks:,} ticks")
        for name, column in history.items():
            if name != "tick":
                print(f"  {name}: {format_value(column[-1])}")
    else:
        from .gui import App, default_title, slider_for

        app = App(model, title or default_title(model))
        if options.speed is not None:
            app.speed = slider_for(options.speed)
        app.stop_at = options.ticks
        app.run(go=options.go)

    if options.csv is not None:
        write_csv(model.history, options.csv)
        print(f"wrote {len(model.history['tick']):,} rows to {options.csv}")
